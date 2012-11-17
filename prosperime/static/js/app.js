// Models

var Org = Backbone.Model.extend();

var OrgList = Backbone.Collection.extend({

	model: Org,


});

// Views

var OrgSingleView = Backbone.View.extend(

	tagName: "li",

	template:_.template($('#org-template').html()),

	initialize: function() {
		this.model.bind('change',this.render,this);
		this.model.bind('destroy',this.remove,this);
	},

	events:{
		"click .view" 		: "fullDisplay",
		"click .dismiss" 	: "dismiss"
	},

	render: function() {
		this.$el.html(this.template(this.model.toJSON()));
	},

	display: function() {

	},

	dismiss: function() {

	},

	schema: {
		location: {type: }
	}

	);

var OrgListView = Backbone.View.extend();