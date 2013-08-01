/* Helpers.js
 *
 * Collection of useful, commonly used methods
 * If not needed at page load, load asynchronously
 * (in case this file gets big)
 */

var min_radius = 14
var max_radius = 55
var range = max_radius - min_radius

var break_string = function(max_chars, string) {

	var last_space = string.substring(0,max_chars).lastIndexOf(" ")
	if (string.substring(last_space).length > max_chars) {
		string = string.substring(0, last_space) + "\n" + string.substring(last_space)
		var second_space = string.substring(last_space+1,last_space+1+max_chars).lastIndexOf(" ")
		return string.substring(0,last_space+second_space+1) + "\n" + string.substring(last_space+second_space+1)
	
	} else
		return string.substring(0, last_space) + "\n" + string.substring(last_space)
};

var get_max_radius = function() {
	return max_radius
};

// Given a total and a proportion, returns the scaled radius
var size_dot = function(total, portion) {
	return ((portion / total) * range) + min_radius
};

// Given a total and an array of portions, returns an in-order 
//	array of scaled radii
var size_dots = function(total, portions) {
	var length = portions.length;
	var vals = []
	for (var i = 0; i < length; i++) {
		vals.push((portions[i] / total) * range) + min_radius
	};
	return vals
};

// Tested on SVG elements specifically, unbinds all events
var unbind_events = function(el) {
	// Unbind Events
	if (el.events) {
		while(el.events.length) {
			var e = el.events.pop()
			e.unbind()
		}
	}
};

// From StackOverflow. Clears elements from a paper
function clearPaper(paper){
    var paperDom = paper.canvas;
    paperDom.parentNode.removeChild(paperDom);
}

function months_difference (mo1, yr1, mo2, yr2, compress, round) {
	var diff = 12 * (yr2 - yr1);
	diff += (mo2 - mo1);

	if(compress) {
		diff = diff / 2
		if (round == "upper") diff = Math.ceil(diff)
		if (round == "lower") diff = Math.floor(diff)
	}
	return diff;
};
