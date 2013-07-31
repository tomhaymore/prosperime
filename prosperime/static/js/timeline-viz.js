
var Timeline = (function() {

    /***********/
    /* Private */
    /***********/

    // Constants
    var offset = 50,
        textBox_offset_top = 150;

    // Instance Variables
    var positions = [],
        w,
        h,
        paper,
        $form,
        timeline_start,
        timeline_end,
        month_offset,
        midline,
        permissions,
        hidden_nodes = [],
        $el;


    function updateNode(position, index) {
        // get textBox in question
        var textBox = $(".timeline-position[data-index='" + index + "']")
        var old_x = parseInt($(textBox).attr("data-x")) + ($(textBox).width() / 2)

        // init template
        var template = _.template($("#timeline-position-fragment-template").html())
        $(textBox).html(template(position))

        // check for new 'x'
        // if it fits, center div
        var half_box = $(textBox).width() / 2
        var x = (old_x - half_box > offset) ? old_x - half_box : old_x;
        x = (old_x + half_box > w) ? old_x - half_box : x;
        $(textBox).attr("data-x", x)
    };

    function createLine() {
        // line attributes
        var line_attr = {"stroke-width":1, "stroke-linecap":"round", "opacity":.8, "stroke":"#777"}
        // create line
        var timeline = paper.path("M" + offset + "," + midline + " L" + (w - offset) + "," + midline).attr(line_attr)
    };

    function createNode(position, index) {
        // local attributes
        var color = "rgb(111,182,212)",
            outer_r = 10,
            inner_r = 2,
            outer_dot_attr = {'stroke-width':'2', 'stroke':color, 'fill':color, 'fill-opacity':'.8' },
            inner_dot_attr = {'stroke-width':'1', 'stroke':color, 'fill':color},
            hidden_dot_attr = {'stroke-width':'1', 'stroke':"#27AE60", 'fill':"#27AE60", cursor:"pointer" },
            hidden_text_attr = {"cursor": "pointer", "font-family":"Helvetica", "font-size":"12pt", "stroke":"none", "fill":"#ECF0F1"};
           
        // calculate 'x' value for nodes
        var months_difference = monthsDifference(timeline_start, position.start_date)
        var x = (months_difference * month_offset) + offset

        // create outer node, add handlers
        var outer_node = paper.circle(x, midline, outer_r)
            .attr(outer_dot_attr)
            .data("index", index)
            .mouseover(nodeMouseover)

    
        // create & hide mouseover node
        var hidden_node = paper.circle(x, midline, outer_r)
            .attr(hidden_dot_attr)
            .hide()
            .data("index", index)
            .mouseout(nodeMouseout)

        // create & hide mouseover text
        var hidden_text = paper.text(x, midline, "Edit")
            .attr(hidden_text_attr)
            .hide()
            // TODO: add mouseout to text as well (for fast transitions)

        // only allow editing given proper permission
        if (permissions.indexOf("w") != -1) {
            hidden_node.click(function(ev) { animateToEdit(ev, index) })
            hidden_text.click(function(ev) { animateToEdit(ev, index) })
        } else {
            // needed for read-only profiles
            outer_node.mouseout(nodeMouseout)
        }

        // set id on outer_node for hover event, hover_node for hover event
        outer_node.data("hidden_node_id", hidden_node.id)
        outer_node.data("hidden_text_id", hidden_text.id)
        hidden_node.data("hidden_text_id", hidden_text.id)

        // append hidden_node_id to g
        hidden_nodes.push(hidden_node.id)
         
        // // create inner node (purely aesthetic)
        // var inner_node = paper.circle(x, midline, inner_r)
        //     .attr(inner_dot_attr)

        // create text box, positioned offscreen
        createTextBox(position, index, x, hidden_node.id)
    };

    // creates single textbox using underscore template, positions offscreen
    function createTextBox(position, index, x, hidden_node_id) {
        // init template
        var template = _.template($("#timeline-position-template").html())
        $("#" + $el).append(template(position))

        // if it fits, center div
        var half_box = $(".timeline-position :last").width() / 2
        x = (x - half_box > offset) ? x - half_box : x;
        x = (x + half_box > w) ? x - half_box : x;

        // reposition offscreen // *NOTE* data must be set as attributes for needed selector to work
        $(".timeline-position :last")
            .attr("data-index", index).attr("data-x", x).attr("data-node-id", hidden_node_id)
            .css("top", textBox_offset_top + "px").css("left", "-500px")
    };

    // runs through all nodes and triggers mouseexit events if needed
    function checkAllNodes() {
        for (i in hidden_nodes) checkSingleNode(paper.getById(hidden_nodes[i]))
    };
    
    // check if the node is in the "hovered" state (=expanded to bigger radius)
        // if so, returns node to normal and moves textBox offscreen
    function checkSingleNode(hidden_node) {
        if (hidden_node.attr("r") > 12) {
            // move box back offscreen
            $(".timeline-position[data-index='" + hidden_node.data("index") + "']").fadeOut(100).css("left", "-500px").show().removeClass("onscreen")

            // hide hover node & text
            if (permissions.indexOf("w") != -1 ) {
                hidden_node.animate({"r":12}, "150", function() { this.hide() });
                paper.getById(hidden_node.data("hidden_text_id")).hide()
            } else {
                hidden_node.animate({"r":12}, 250)
            }   
        };
    };

    // triggered on SVG circles (=this)
    function nodeMouseover(e) {

        // get textBox (currently hidden offscreen)
        var textBox = $(".timeline-position[data-index='" + this.data("index") + "']")
        // make sure not already triggered
        if ($(textBox).hasClass("onscreen"))
            return false;

        // HACK: check that other nodes aren't already fired (from quick mousing)
        checkAllNodes()

        // get 'x' value for textbox, move it to new location
        var x = parseInt($(textBox).attr("data-x"))
        var container_offset = parseInt($("#" + $el).offset().left)
        $(textBox).hide().css("left", (x + container_offset) + "px").fadeIn(200).addClass("onscreen")

        // show hover elements (green circle, text)
        if (permissions.indexOf("w") != -1) {
            paper.getById(this.data("hidden_node_id")).show().animate({"r":18}, 200)
            paper.getById(this.data("hidden_text_id")).show()
        } else {
            this.animate({"r":18}, 250)
        }
    }

    // triggered on hover node (green SVG circle)
    function nodeMouseout(e) {
        // make sure moused completely out
        if (e.toElement.tagName == "circle" || e.toElement.tagName == "tspan")
            return false;

        // move box back offscreen
        $(".timeline-position[data-index='" + this.data("index") + "']").fadeOut(100).css("left", "-500px").show().removeClass("onscreen")

        // hide hover node & text
        if (permissions.indexOf("w") != -1 ) {
            this.animate({"r":12}, "150", function() { this.hide() });
            paper.getById(this.data("hidden_text_id")).hide()
        } else {
            this.animate({"r":12}, 250)
        }
    }

    function animateToEdit(ev, index) {

        var textBox = $(".timeline-position[data-index='" + index + "']")

        var form_container = $("#" + $form)
        textBox.animate({"top":$(form_container).offset().top}, 250, function() {
            // hide textBox
            $(textBox).fadeOut(200).css("left", "-500px").css("top", textBox_offset_top + "px").show()
            // show form 
            renderEditForm(positions[index]) // code in [profile.html]
        })

    };

    function monthsDifference(d1, d2) {
        var m1 = parseInt(d1.substring(0,2)),
            y1 = parseInt(d1.substring(3)),
            m2 = parseInt(d2.substring(0,2)),
            y2 = parseInt(d2.substring(3)),
            diff = (12 * (y2 - y1)) + (m2 - m1)
        return Math.round(diff);
    }; 


    /**********/
    /* Public */
    /**********/
    return {

        init: function(data, container, container_width, container_height, form_container, _permissions) {
            // sort and set positions
            positions = _.sortBy(data[0], function(p) {
                return p.start_date.substring(3) + p.start_date.substring(0,2)              
            });
            // set instance vars
            permissions = _permissions
            timeline_start = data[1]
            timeline_end = data[2]
            $el = container
            w = container_width
            h = container_height
            $form = form_container
            midline = h - 25
            month_offset = Math.floor((w - (offset * 2)) / data[3])

            // create and store paper
            paper = new Raphael($el, w, h)
        },

        construct: function() {
            // create line
            createLine()
            // create positions & text boxes
            for (p in positions) {
                createNode(positions[p], p)
            }

        },

        editPosition: function(edited_position) {
            // grab edited position
            for (p in positions) {
                if (edited_position.id == positions[p].id) {
                    positions[p] = edited_position
                    console.log(positions[p])
                    updateNode(edited_position, p)
                    break;
                }
            }
        },

        addPosition: function(position) {
            positions.push(position)
            console.log(positions[0])
            console.log(position)
            createNode(position, positions.length - 1)
        },

        // Returns Timeline to original state (no events firing or fired)
        normalize: function() {
            checkAllNodes()
        },
    }
}());

