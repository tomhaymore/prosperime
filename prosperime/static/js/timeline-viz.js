




var monospaced_timeline = function(constants, positions, el) {
    console.log(el)
	/* Default Constants */
	var outer_dot_radius = (constants['outer_dot_radius']) ? constants['outer_dot_radius'] : 12;
	var inner_dot_radius = (constants['inner_dot_radius']) ? constants['inner_dot_radius'] : 2;
	var color = "rgb(51,121,202)"
	var padding = (constants['padding']) ? constants['padding'] : 5;
	var timeline_color = (constants['timeline_color']) ? constants['timeline_color'] : "#c0c0c0"
	var text_attributes = (constants['text_attributes']) ? constants['text_attributes'] : {'font-size':12, 'font-family':'"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif'}
	var position_text_height = (constants['position_text_height']) ? constants['position_text_height'] : 20;

	// **These values must be supplied**
	var paper_w = constants['paper_w']
	var paper_h = constants['paper_h']
	var start_offset = constants['start_offset']
	var midline = constants['midline']



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

                // Create text
                var position_entity = paper.text(x, 17, positions[j].org).attr(text_attributes)
                var position_title = paper.text(x, 10, positions[j].title).attr(text_attributes)
                
                // Ensures box is big enough
                if (positions[j].org.length > positions[j].title.length) var width = positions[j].org.length * 7
                else var width = positions[j].title.length * 7;

                var y_start = midline - outer_dot_radius
                var y_1 = midline - outer_dot_radius - padding
                var y_2 = midline - outer_dot_radius - position_text_height - padding
                break;

            case 1:

                // Create text
                var position_entity = paper.text(x, 48, positions[j].org).attr(text_attributes)
                var position_title = paper.text(x, 55, positions[j].title).attr(text_attributes)
                
                // Ensures box is big enough
                if (positions[j].org.length > positions[j].title.length) var width = positions[j].org.length * 7
                else var width = positions[j].title.length * 7;
                
                var y_start = midline + outer_dot_radius
                var y_1 = midline + outer_dot_radius + padding
                var y_2 = midline + outer_dot_radius + position_text_height + padding
                break;
        }

        // Create box
        var position_title_box = paper.path(
            // "M" + x + ", " + y_start + " " + 
            // "L" + (x + 5) + ", " + y_1 + " " +
            // "L" + (x + (width / 2)) + ", " + y_1 + " " + 
            // "L" + (x + (width / 2)) + ", " + y_2 + " " +
            // "L" + (x - (width / 2)) + ", " + y_2 + " " +
            // "L" + (x - (width / 2)) + ", " + y_1 + " " + 
            // "L" + (x - 5) + ", " + y_1 + " " + 
            // "L" + x + ", " + y_start + " "

            "M" + (x+(width/2)) + ", " + y_1 + " " + 
            "L" + (x+padding) + ", " + y_1 + " " + 
            "L" + x + ", " + y_start + " " +
            "L" + (x-padding) + ", " + y_1 + " " + 
            "L" + (x-(width/2)) + ", " + y_1
        )

    }


}; 