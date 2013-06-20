var vertical_timeline = function() {
		/*********************/
		/* VERTICAL TIMELINE */
		/*********************/

		// Get Metadata
		var positions = $('#position-data-structure')
		var num_positions = positions.children().length
		if (num_positions == 0) return false;
	
		console.log('num positions: ' + num_positions)
		console.log('equal offset: ' + equal_offset)

		var metadata = $('#metadata')
		var total_start_date = metadata.children()[0].innerHTML
		var total_end_date = metadata.children()[1].innerHTML
		var total_time = metadata.children()[2].innerHTML

		/* CONSTANTS */

		// Info Box
		var info_box_buffer = 15
		var info_box_width = 300
		var info_box_height = 100
		// var equal_offset = (vertical_timeline_length / (num_positions + 1))
		var equal_offset = info_box_height + (2 * info_box_buffer)

		// Pic
		// var pic_width = Math.ceil(info_box_width / 4)
		// var pic_height = (equal_offset - info_box_buffer - 5) * .75
		var pic_width = 75
		var pic_height = 50
		
		// Description Box
		var description_box_width = 400
		var description_box_height = 400

		// Timeline
		var vertical_timeline_start_offset = 75
		var vertical_timeline_length = num_positions * equal_offset + vertical_timeline_start_offset
		console.log('timeline length = ' + vertical_timeline_length)

		/* Create SVG Elements */
		// Create Paper
		var paper_width = 1000
		var paper_height = vertical_timeline_length + 200
		var paper = new Raphael('timeline-container', paper_width, paper_height)

		
		// Timeline
		var main_timeline = paper.path('M100,'+vertical_timeline_start_offset+' L100,'+(vertical_timeline_start_offset + vertical_timeline_length)).attr({
			'stroke':'#555',
			'stroke-dasharray':'2, 2'
		})

		
		// End Date Rectangle
		var top_rect = paper.rect(50, vertical_timeline_start_offset - 30, 100, 30, 2).attr({
			'stroke':'#c0c0c0',
			'stroke-width':'1',
			'fill':'rgb(41,98,152)',
			// 'fill-opacity':0.7,
		})

		// End Date Rectangle Text
		var top_rect_text = paper.text(100, vertical_timeline_start_offset - 15, 'Present')
		top_rect_text.attr({
			'font-size':'14pt',
			'stroke':'#fffffe',
			'font-weight':'200',
			'font-family': '"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
		})
		top_rect_text.node.setAttribute('class','loose-spacing')

		// Start Date Rectangle
		var bottom_rect = paper.rect(50, vertical_timeline_start_offset + vertical_timeline_length, 100, 30, 2)
		bottom_rect.attr({
			'stroke':'#c0c0c0',
			'fill':'rgb(41,98,152)',
			// 'fill-opacity':0.7,
		})

		// Start Date Rectangle Text
		var bottom_rect_text = paper.text(100, vertical_timeline_start_offset + vertical_timeline_length + 15, total_start_date)
		bottom_rect_text.attr({
			'font-size':'14px',
			'stroke':'#fffffe',
			'font-weight':'200',
			'font-family': '"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
		})
		bottom_rect_text.node.setAttribute('class','loose-spacing')


		var previous_end = vertical_timeline_start_offset
		// Add position dots
		for (var i = num_positions; i > 0; i--) {

			// Get Position data
			var wrapper = positions.children()[i - 1]
			var type = wrapper.childNodes[1].innerHTML
			var title = wrapper.childNodes[3].innerHTML
			var entity_name = wrapper.childNodes[5].innerHTML
			var id = wrapper.childNodes[7].innerHTML
			var description = wrapper.childNodes[9].innerHTML
			var start_date = wrapper.childNodes[11].innerHTML
			var end_date = wrapper.childNodes[13].innerHTML
			var pic = wrapper.childNodes[15].innerHTML
			console.log(pic)

			var color = 'rgb(50,121,202)'
			if (type == 'education') color = 'rgb(191,51,48)'
			if (type == 'internship') color = 'rgb(255,195,64)'


			// Outer Dot
			var y = 50 + (equal_offset * i)
			var outer_dot = paper.circle(100, y, 12)
			outer_dot.attr({
				'stroke-width':'1',
				'stroke':'rgb(50,121,202)',
				'fill':'none',
			});

			// Inner Dot
			var dot = paper.circle(100, y, 7)
			dot.attr({
				'stroke-width':1,
				'stroke':'rgb(50,121,202)',
				'fill':'rgb(50,121,202)',
				'fill-opacity':'.4',
			})

			if (type == 'education') {
				outer_dot.attr({'stroke':'rgb(191,51,48)'})
				dot.attr({'stroke':'rgb(191,51,48)', 'fill':'rgb(191,51,48)'})
			} else if (type == 'internship') {
				outer_dot.attr({'stroke':'rgb(255,195,64)'})
				dot.attr({'stroke':'rgb(255,195,64)', 'fill':'rgb(255,195,64)'})
			} else type = 'position' //'org' not good for display

			// // Timeline chunk
			// if (i == num_positions) {
			// 	var top = previous_end
			// 	var bottom = previous_end + equal_offset - 50
			// 	console.log('s: ' + top + ' e: '+ bottom)
			// }

			// var path = paper.path('M100,' + top + ' L100,' + bottom).attr({'stroke':'#555'})
			// 	previous_end = top + 32


			var box_offset = (equal_offset - info_box_buffer) / 2
			var info_box = paper.path('M112,' + y + ' L117,' + (y-5) + 'L117,' + (y - box_offset) + ' L' + (117 + info_box_width) + ', ' + (y - box_offset) + ' L' + (117 + info_box_width) + ', ' + (y + box_offset) + ' L117,' + (y + box_offset) + ' L117,' + (y+5) + ' L112,' + y)
			


			var info_box_header_line = paper.path('M117,' + (y - box_offset + 20) + ' L' + (117 + info_box_width) + ',' + (y - box_offset + 20))

			// // If profile pic, throw it in there
			// if (pic.indexOf('none') == -1) {
			
			// 	var image = paper.image('../media/'+pic, 120, y - box_offset + 25, pic_width, pic_height)
				
			// }

			var info_box_dates = paper.text(155,(y - box_offset + 10), format_date(start_date) + '/' + format_date(end_date)).attr({
					'font-family':'"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
					'font-size':'12px',
				})

			var info_box_type = paper.circle(119 + (info_box_width) - 20, (y - box_offset + 10), 4).attr({
					'stroke':color,
					'fill':color
			})


			var info_box_title = paper.text(117 + (info_box_width / 2), y - 10, title)
			info_box_title.node.setAttribute('class','info_box_text')
			info_box_title.attr({
				'font-family': '"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
				'font-size':'14px',
				'font-weight':'500'
			})

			var info_box_entity_name = paper.text(117 + (info_box_width / 2), y + 20, entity_name)
			info_box_entity_name.node.setAttribute('class','info_box_text')
			info_box_entity_name.attr({
				'font-family': '"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
				'font-size':'14px',
				'font-weight':'500'
			})

			if (info_box_title.getBBox().width > info_box_width || info_box_entity_name.getBBox().width > info_box_width) {
				console.log('that shit is too long')
			}

			dot.data('description', description)
			dot.data('color', color)
			dot.data('y', y)
			type = type.charAt(0).toUpperCase() + type.slice(1);
			dot.data('type', type)
			dot.data('title', title)
			dot.data('entity_name', entity_name)


			// On hover to dots
			dot.hover(function() {
				// Remove old boxes
				if ($('#description_box').length > 0) {
					$('#description_box').remove()
					$('#description_box_header').remove()
					$('#description_box_header_line').remove()
					$('#description_box_header_info').remove()
				}

				// Add new box
				var start_x = 117 + info_box_width
				var description_box = paper.path(
					'M' + start_x + ', ' + this.data('y') + 
					' L' + (start_x + 15) + ',' + (this.data('y') - 15) +
					' L' + (start_x + 15) + ',' + (this.data('y') - 15 - (description_box_height / 3)) +
					' L' + (start_x + 15 + description_box_width) + ', ' + (this.data('y') - 15 - (description_box_height / 3)) + 
					' L' + (start_x + 15 + description_box_width) + ', ' + (this.data('y') - 15 + description_box_height / 3) + 
					' L' + (start_x + 15) + ', ' + (this.data('y') - 15 + description_box_height / 3) + 
					' L' + (start_x + 15) + ', ' + (this.data('y') + 15) + 
					' L' + start_x + ', ' + this.data('y')
					).attr({
						'stroke-linejoin':'miter',
					})


				// Add header line
				var description_box_header_line = paper.path(
					'M' + (start_x + 15) + ', ' + (this.data('y') - 15 - (description_box_height / 3) + 30) + ' L' + (start_x + 15 + description_box_width) + ', ' + (this.data('y') - 15 - (description_box_height / 3) + 30))

				// Add header info
				var description_box_header = paper.text((start_x + 55), (this.data('y') - (description_box_height / 3) + 3), this.data('type')).attr({
						'font-size':'14pt',
						'font-family': '"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
						'stroke':this.data('color')
				})
				description_box_header.node.setAttribute('class','loose-spacing')

				var description_box_header_info = paper.text((start_x + 100), (this.data('y') - (description_box_height / 3) + 3), (this.data('title') + ' at ' + this.data('entity_name'))).attr({
						'font-size':'14pt',
						'font-family': '"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
						'text-anchor':'start'
					})			

				// // Add content to the box
				// var description_box_header = paper.text((start_x + ((15 + description_box_width) / 2)), (this.data('y') - (description_box_height / 3) + 30), 'A description of said position').attr({
				// 	'font-size':'12pt',
				// 	'font-family': '"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
				// })
				// description_box_header.node.id = 'description_box_header'

				// Set ID's so they can be erased
				description_box.node.id = 'description_box'
				description_box_header_line.node.id = 'description_box_header_line'
				description_box_header.node.id = 'description_box_header'
				description_box_header_info.node.id = 'description_box_header_info'

			},
			function() {

			});
	
 		}
 	}


 /* Used in profile pages. Onmouseover event renders the description
	   for a given element in the element id='middle-float-screen' */
	var showDescription = function(index, title, co_name, start_date, end_date) {
		// Don't override the prompt!
		if ($('#career-decision-module').length > 0) {
			console.log('got in here')
			return false;
		}

		// Empty what's in the float screen
		$('#middle-float-screen').empty()
		// If no description, will throw exception
		try {
			// Couldn't get this to work in JQ so stopped trying
			var description = document.getElementsByClassName('timeline-description-text')[index].innerHTML
			var newText = "<div class='box-header'>"
			if (title) newText += title
			if (co_name) newText += ' at ' + co_name
			newText += "</div>"
			if (start_date) {
				newText += "<div class='box-dates'>"
				newText += start_date.replace('1, ','')
				newText += ' - '
				if (end_date == "Current") newText += "Current"
				else newText += end_date.replace('1, ', '')
				newText += "</div>"
			}

			if (description) newText += "<div class='box-description'>" + description + "</div>"
		} catch (err) {
			var newText = '<a>For more information, hover over a position</a>'
		}
		$('#middle-float-screen').html(newText);
	};