
// kick off app once DOM is ready

$(function(){

	// Models

	// Param: dynamically loaded search param

	window.Param = Backbone.Model.extend({


	});

	// Org: search result form for organizations

	window.Org = Backbone.Model.extend();

	// Collections

	window.Params = Backbone.Collection.extend({

		model:Param,
	})

	window.Orgs = Backbone.Collection.extend({

		model: Org,
		url: '/companies'

	});

	window.orgs = new Orgs;

	// Views

	window.OrgSingleView = Backbone.View.extend({

		// tag: "div",

		template:_.template($('#org-single-template').html()),

		initialize: function() {
			this.model.on('change',this.render,this);
			//this.template = _.template($('#org-single-template').html())
		},

		render: function() {
			// var renderedContent = $(this.el).html(this.template(this.model.toJSON()));
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		}

	});

	window.OrgListView = Backbone.View.extend({
		el: $('#org-list'),
		tag: "div",
		template: _.template($('#org-list-template').html()),

		initialize: function() {
			_.bindAll(this,'render');
			this.collection.bind('reset',this.render);
			// this.template = _.template($('#org-list-template').html());
		},

		render: function() {
			var $orgs,
				collection = this.collection;

			$(this.el).html(this.template({}));
			$orgs = this.$(".org-list");
			this.collection.each(function(org) {
				var view = new OrgSingleView({
					model: org,
					collection: collection
				});
				$orgs.append(view.render().el);
			});
			return this;
		}
	});

});



