

var timeline_box_titles_data = []
var debug = false;

var constants = {

    'bootstrap_fonts':'"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',

    'education_color': '#bf3330',
    'internship_color': '#ffc340',
    'position_color': 'rgb(50,121,202)',

    'title_font_size':'12',
    'line-height':30,

    'lvl1_offset':45,
    'lvl2_offset':75,

    'lvl1_offset_condensed':20,
}


var construct_timeline_title = function(paper, entity_name, start_offset, dot_id) {

    var text_attr = {
        'font-size':constants.title_font_size,
        'font-family':constants.bootstrap_fonts,
    }

    var text = paper.text(0,0,entity_name).attr(text_attr)
    timeline_box_titles_data.push({'id':text.id, 'start_offset':start_offset, 'dot_id':dot_id})

    text.attr("font-size", "13") // no idea why this hasn't been working

    return text
};

var reposition_titles = function(paper) {

    var padding = 10
    var previous_x_above = -100
    var previous_x_below = -100
    var previous_x_above_lvl1 = true
    var previous_x_below_lvl1 = true

    // Sort by start offset
    timeline_box_titles_data = _.sortBy(timeline_box_titles_data, function(el) {
        return el['start_offset']
    })
    
    for (var y = 0; y < timeline_box_titles_data.length; y++) {
        var current_text = paper.getById(timeline_box_titles_data[y].id)
        if (y % 2 == 0) {
            if (debug) console.log("Current start: " + (timeline_box_titles_data[y]['start_offset'] - (current_text.getBBox().width / 2)) + " | Previous End: " + previous_x_above)

            // Above
            if (timeline_box_titles_data[y]['start_offset'] - (current_text.getBBox().width / 2) > previous_x_above) {
                // space, go to lvl1
                previous_x_above_lvl1 = true 
            } else if (!previous_x_above_lvl1) {
                previous_x_above_lvl1 = true
            } else {
                previous_x_above_lvl1 = false;
            }

            if (previous_x_above_lvl1) {
                // then lvl 1
                if (debug) console.log("Above, lvl1: " + current_text.attr("text"))
                reposition_title_box(paper, 0, timeline_box_titles_data[y]['start_offset'], timeline_box_titles_data[y]['id'])
           } else {
                 // then lvl 2
                reposition_title_box(paper, 2, timeline_box_titles_data[y]['start_offset'], timeline_box_titles_data[y]['id'])
                if (debug) console.log("Above, lvl2: " + current_text.attr("text"))
            }
            previous_x_above = timeline_box_titles_data[y]['start_offset'] + (current_text.getBBox().width / 2) + padding

        } else {
            // Below
            if (debug) console.log("Current start: " + (timeline_box_titles_data[y]['start_offset'] - (current_text.getBBox().width / 2)) + " | Previous End: " + previous_x_below)

            if (timeline_box_titles_data[y]['start_offset'] - (current_text.getBBox().width / 2) > previous_x_below) {
                previous_x_below_lvl1 = true
            } else if (!previous_x_below_lvl1) {
                previous_x_below_lvl1 = true
            } else {
                previous_x_below_lvl1 = false
            }

            if (previous_x_below_lvl1) {
                // lvl 1
                if (debug) console.log("Below, lvl1: "  + current_text.attr("text"))
                reposition_title_box(paper, 1, timeline_box_titles_data[y]['start_offset'], timeline_box_titles_data[y]['id'])

            } else {
                // lvl 2
               if (debug) console.log("Below, lvl2: " + current_text.attr("text"))
                reposition_title_box(paper, 3, timeline_box_titles_data[y]['start_offset'], timeline_box_titles_data[y]['id'])
            }  
            previous_x_below = timeline_box_titles_data[y]['start_offset'] + (current_text.getBBox().width / 2) + padding
        }
    }
};


var get_color = function(type) {

    switch(type) {
        case 'education':
            return constants.education_color
            break;
        case 'internship':
            return constants.internship_color
            break;
        default:
            return constants.position_color
    };
}


var add_selector_circles = function(paper) {

    var position_select_dot = paper.circle(850,15,12).attr({
        'fill':get_color("position"),
        'stroke-width':0,
        'opacity':.5,
    });
    position_select_dot.node.id="position-selector"
    var internship_select_dot = paper.circle(880, 15, 12).attr({
        'fill':get_color("internship"),
        'stroke-width':0,
        'opacity':.5,
    });
    internship_select_dot.node.id = "internship-selector"
    var education_select_dot = paper.circle(910, 15, 12).attr({
        'fill':get_color("education"),
        'stroke-width':0,
        'opacity':.5,
    });
    education_select_dot.node.id = "education-selector"

    var select_text = paper.text(880, 35, "Position Type")
    var select_text_id = select_text.id

    var selector_hover_over = function(ev) {
        var type = $(ev.currentTarget).attr("id")
        alterDotOpacities(paper, type, 0.1, "#c0c0c0", 4)
        paper.getById(select_text_id).attr("text", type.split('-')[0].charAt(0).toUpperCase() + type.split('-')[0].slice(1))
        
    };

    var selector_hover_out = function(ev) {
        var type = $(ev.currentTarget).attr("id")
        alterDotOpacities(paper, type, 0.8, "#fffffe", 0)       
    };

    // Assign Hover Handlers
    position_select_dot.hover(selector_hover_over, selector_hover_out)
    internship_select_dot.hover(selector_hover_over, selector_hover_out)
    education_select_dot.hover(selector_hover_over, selector_hover_out)
}


/* Helper fxn constructs title boxes for timeline based on index
        of current position */
    var reposition_title_box = function(paper, index, offset, text_id) {

        if (index % 4 == 0) var level = 1
        else if (index % 4 == 1) var level = 3
        else if (index % 4 == 2) var level = 4
        else var level = 2


        var position_title
        var width
        var y_start
        var y_1
        var y_2
        var base = 100
        var line_height = constants.line_height
        var timeline_start = 100

        var title_attr = {
            'font-size':constants.info_font_size,
            'font-family':constants.font_family,
        }

        var position_title = paper.getById(text_id)
        position_title.attr("x", timeline_start + offset)
        position_title.attr("y", timeline_start - constants.
            lvl1_offset)

        switch(level) {
            case 1:
                width = position_title.getBBox().width
                y_start = base - constants.outer_dot_radius - 8 // 88
                y_1 = base - line_height // 80
                y_2 = base - (2 * line_height) // 60
                position_title.attr("y", timeline_start - constants.lvl1_offset)

                break;

            case 2:
                width = position_title.getBBox().width
                y_start = base + line_height + constants.outer_dot_radius + 8 // 132
                y_1 = base + (2 * line_height) // 140
                y_2 = base + (3 * line_height) // 160
                position_title.attr("y", timeline_start + constants.lvl2_offset)
                break;

            case 3:
                width = position_title.getBBox().width
                y_start = base + constants.outer_dot_radius + 8
                y_1 = base + line_height
                y_2 = base + (2 * line_height)
                position_title.attr("y", timeline_start + constants.lvl1_offset)
                break;

            case 4:
                width = position_title.getBBox().width
                y_start = base - line_height - constants.outer_dot_radius - 8
                y_1 = base - (2 * line_height)
                y_2 = base - (3 * line_height)
                position_title.attr("y", timeline_start - constants.lvl2_offset)
                break;
        }
        var position_title_container = paper.path(
                    'M' + (constants.timeline_start + offset) + ', ' + y_start + ' ' + 
                    'L' + (constants.timeline_start + offset + 4) + ', ' + y_1 + ' ' +
                    'L' + (constants.timeline_start + offset + (width / 2) + 7) + ', ' + y_1 + ' ' +  
                    'L' + (constants.timeline_start + offset + (width / 2) + 7) + ', ' + y_2 + ' ' + 
                    'L' + (constants.timeline_start + offset - (width / 2) - 7) + ', ' + y_2 + ' ' + 
                    'L' + (constants.timeline_start + offset - (width / 2) - 7) + ', ' + y_1 + ' ' +  
                    'L' + (constants.timeline_start + offset - 4) + ', ' + y_1 + ' ' +  
                    'L' + (constants.timeline_start + offset) + ', ' + y_start
                    )


        position_title.attr({
            'font-variant':'small-caps',
            'font-family': constants.bootstrap_fonts,
        })

        return position_title
    }


/* Helper fxn constructs title boxes for timeline based on index
        of current position */
    var construct_title_box = function(paper, index, entity_name, offset) {

        if (index % 4 == 0) var level = 1
        else if (index % 4 == 1) var level = 3
        else if (index % 4 == 2) var level = 4
        else var level = 2

        // console.log('index ' + index + ' ' + entity_name + ' ' + level)

        var position_title
        var width
        var y_start
        var y_1
        var y_2
        var base = 100
        var line_height = constants.line_height

        var title_attr = {
            'font-size':constants.info_font_size,
            'font-family':constants.font_family,
        }

        switch(level) {
            case 1:
                position_title = paper.text(constants.timeline_start + offset, constants.timeline_y - constants.lvl1_offset, entity_name).attr(title_attr)
                width = position_title.getBBox().width
                y_start = base - constants.outer_dot_radius// 88
                y_1 = base - line_height // 80
                y_2 = base - (2 * line_height) // 60

                break;

            case 2:
                position_title = paper.text(constants.timeline_start + offset, constants.timeline_y + constants.lvl2_offset, entity_name).attr(title_attr)
                width = position_title.getBBox().width
                y_start = base + line_height + constants.outer_dot_radius// 132
                y_1 = base + (2 * line_height) // 140
                y_2 = base + (3 * line_height) // 160

                break;

            case 3:
                position_title = paper.text(constants.timeline_start + offset, constants.timeline_y + constants.lvl1_offset, entity_name).attr(title_attr)
                width = position_title.getBBox().width
                y_start = base + constants.outer_dot_radius
                y_1 = base + line_height
                y_2 = base + (2 * line_height)

                break;

            case 4:
                position_title = paper.text(constants.timeline_start + offset, constants.timeline_y - constants.lvl2_offset, entity_name).attr(title_attr)
                width = position_title.getBBox().width
                y_start = base - line_height - constants.outer_dot_radius
                y_1 = base - (2 * line_height)
                y_2 = base - (3 * line_height)

                break;
        }
        var position_title_container = paper.path(
                    'M' + (constants.timeline_start + offset) + ', ' + y_start + ' ' + 
                    'L' + (constants.timeline_start + offset + 4) + ', ' + y_1 + ' ' +
                    'L' + (constants.timeline_start + offset + (width / 2) + 7) + ', ' + y_1 + ' ' +  
                    'L' + (constants.timeline_start + offset + (width / 2) + 7) + ', ' + y_2 + ' ' + 
                    'L' + (constants.timeline_start + offset - (width / 2) - 7) + ', ' + y_2 + ' ' + 
                    'L' + (constants.timeline_start + offset - (width / 2) - 7) + ', ' + y_1 + ' ' +  
                    'L' + (constants.timeline_start + offset - 4) + ', ' + y_1 + ' ' +  
                    'L' + (constants.timeline_start + offset) + ', ' + y_start
                    )


        position_title.attr({
            'font-variant':'small-caps',
            'font-family': constants.bootstrap_fonts,
        })

        return position_title
    }




var monospaced_timeline = function(constants, positions, el) {

    // **These values must be supplied**
    var paper_w = constants['paper_w']
    var paper_h = constants['paper_h']
    var start_offset = constants['start_offset']
    var midline = constants['midline']


	/* Default Constants */
	var outer_dot_radius = (constants['outer_dot_radius']) ? constants['outer_dot_radius'] : 12;
	var inner_dot_radius = (constants['inner_dot_radius']) ? constants['inner_dot_radius'] : 2;
	var color = "rgb(51,121,202)"
	var padding = (constants['padding']) ? constants['padding'] : 5;
	var timeline_color = (constants['timeline_color']) ? constants['timeline_color'] : "#c0c0c0"
	var text_attributes = (constants['text_attributes']) ? constants['text_attributes'] : {'font-size':12, 'font-family':'"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif'}
	var position_text_height = (constants['position_text_height']) ? constants['position_text_height'] : 30;
    var box_style = (constants['box_style']) ? constants['box_style'] : 1;
    var inner_box_offset = (constants['inner_box_offset']) ? constants['inner_box_offset'] : 30;
    var outer_box_offset = inner_box_offset * 2
    var top_text_offset = (constants["top_text_offset"]) ? constants["top_text_offset"] : 25;
    var bottom_text_offset = (constants["bottom_text_offset"]) ? constants["bottom_text_offset"] : 15;
    var effective_midline  = constants["effective_midline"] ? constants["effective_midline"] : midline
        // Note: this is only relevant rendering on positions pages, in
        //       which the y values are screwy for some reason

	var equal_offset = Math.ceil((paper_w - start_offset) / (positions.length + 1))
	var paper = new Raphael(el, paper_w, paper_h)
	var timeline = paper.path("M" + start_offset + "," + midline + " L" + (paper_w - start_offset) + "," + midline).attr({
        "stroke-width":1,
        "stroke-linecap":"round",
        "opacity":.8,
        "stroke":timeline_color,
    })

	// Main Loop - Add dot for each position
    for (var j = 0; j < positions.length; j++) {

        var x = equal_offset * (j + 1)

        // Outer Dot
        var outer_dot = paper.circle(x, midline, outer_dot_radius).attr({
            'stroke-width':'1',
            'stroke':color,
            'fill':color,
            'fill-opacity':'.8',
        });

        // // Something to demarate Ideal Position
        // if (positions[j].title == this.position_title)
        //     outer_dot.attr({
        //         'stroke-width':'1',
        //         'stroke':color,
        //         'fill':color,
        //         'fill-opacity':'0',
        //     })

        // Inner Dot
        var inner_dot = paper.circle(x, midline, inner_dot_radius).attr({
            'stroke-width':1,
            'stroke':color,
            'fill':color,
        })

        // Make Title Box
        if (j % 2 == 0) var index = 0
        else var index = 1

        switch(index) {
            case 0:
                var base = midline - inner_box_offset
                
                // Ensures box is big enough
                if (positions[j].org.length > positions[j].title.length) var width = positions[j].org.length * 7
                else var width = positions[j].title.length * 7;

                var y_start = midline - outer_dot_radius
                var y_1 = midline - outer_dot_radius - padding
                var y_2 = midline - outer_dot_radius - position_text_height - padding
                
                // Create text //17,10
                var position_entity = paper.text(x, (effective_midline-top_text_offset), positions[j].org).attr(text_attributes)
                var position_title = paper.text(x, (effective_midline-bottom_text_offset), positions[j].title).attr(text_attributes)
                break;

            case 1:
                var base = midline + inner_box_offset

                // Ensures box is big enough
                if (positions[j].org.length > positions[j].title.length) var width = positions[j].org.length * 7
                else var width = positions[j].title.length * 7;
                
                var y_start = midline + outer_dot_radius
                var y_1 = midline + outer_dot_radius + padding
                var y_2 = midline + outer_dot_radius + position_text_height + padding
                
                // Create text //48,55
                var position_entity = paper.text(x, (effective_midline+top_text_offset), positions[j].org).attr(text_attributes)
                var position_title = paper.text(x, (effective_midline+bottom_text_offset), positions[j].title).attr(text_attributes)
                break;
        }

        // Create box
        switch(box_style) {

            // Full Box
            case 1:
                var position_title_box = paper.path(
                    "M" + x + ", " + y_start + " " + 
                    "L" + (x + 5) + ", " + y_1 + " " +
                    "L" + (x + (width / 2)) + ", " + y_1 + " " + 
                    "L" + (x + (width / 2)) + ", " + y_2 + " " +
                    "L" + (x - (width / 2)) + ", " + y_2 + " " +
                    "L" + (x - (width / 2)) + ", " + y_1 + " " + 
                    "L" + (x - 5) + ", " + y_1 + " " + 
                    "L" + x + ", " + y_start + " "
                )
                break;

            // Only bottom part 
            case 2:
                var position_title_box = paper.path(
                    "M" + (x+(width/2)) + ", " + y_1 + " " + 
                    "L" + (x+padding) + ", " + y_1 + " " + 
                    "L" + x + ", " + y_start + " " +
                    "L" + (x-padding) + ", " + y_1 + " " + 
                    "L" + (x-(width/2)) + ", " + y_1
                )
                break;

            case 3:
                break;
        }

    }
}; 