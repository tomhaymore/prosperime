/* Helpers.js
 *
 * Collection of useful, commonly used methods
 * If not needed at page load, load asynchronously
 * (in case this file gets big)
 */

var min_radius = 14
var max_radius = 55
var range = max_radius - min_radius

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
