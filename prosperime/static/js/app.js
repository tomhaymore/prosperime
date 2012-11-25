
// kick off app once DOM is ready

$(function(){

	// Models

	// Filter: dynamically loaded search param

	window.Filter = Backbone.Model.extend({


	});

	// Org: search result form for organizations

	window.Org = Backbone.Model.extend();

	// Collections

	// Filters: collection of filters

	window.Filters = Backbone.Collection.extend({

		model:Filter,
		url: '/filters'
	})

	// Orgs: collection of orgs

	window.Orgs = Backbone.Collection.extend({

		model: Org,
		url: '/companies'

	});

	// instantiate collections

	window.orgs = new Orgs;
	window.filters = new Filters;

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
		
		//el: $('#org-list'),
		el: $('#search-results-list'),
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

	window.FilterSingleView = Backbone.View.extend ({
		tagName: 'li',
		template: _.template($("#search-filters-template").html()),

		initialize: function() {
			this.model.on('change',this.render,this);
		},

		render: function() {
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		},

		events: {
			"click input.filter" : "filter"
		},

		filter: function() {
			// create array of all selected filters
			var urlParams;

			var locationFilters = $("input[name='Location-filters']:checked").map(function(filter) { return this.value });
			var sectorFilters = $("input[name='Sector-filters']:checked").map(function(filter) { return this.value });
			var sizeFilters = $("input[name='Size-filters']:checked").map(function(filter) { return this.value });
			var stageFilters = $("input[name='Stage-filters']:checked").map(function(filter) { return this.value });
			
			// construct URL
			
			for (var i = 0; i < locationFilters.length; i++) {
				if (i == 0) {
					urlParams = "loc=" + encodeURIComponent(locationFilters[i]);
				} else {
					urlParams += "&loc=" + encodeURIComponent(locationFilters[i]);
				}
			}	

			for (var i = 0; i < sectorFilters.length; i++) {
				urlParams += "&sector=" + encodeURIComponent(sectorFilters[i]);
			}

			for (var i = 0; i < sizeFilters.length; i++) {
				urlParams += "&size=" + encodeURIComponent(sizeFilters[i]);
			}
			for (var i = 0; i < stageFilters.length; i++) {
				urlParams += "&stage=" + encodeURIComponent(stageFilters[i]);
			}

			filterUrl = "/search/?" + urlParams

			// trigger router to navigate

			this.navigate(filterUrl,{trigger:true});

		}
	});

	window.FilterListView = Backbone.View.extend ({

		el: $("#search-container"),
		tagName: 'div',
		template: _.template($("#search-module-template").html()),

		initialize: function() {
			_.bindAll(this,'render');
			this.collection.bind('reset',this.render);

		},

		render: function() {
			var $filters,
				filterCategories,
				collection = this.collection;

			$(this.el).empty();
			$(this.el).append(_.template($("#search-header-template").html()));
			
			// putll out unique list of categories
			categories = filters.map(function(model) { return model.get('category'); });
			categories = _.uniq(categories);
			for (var i = 0; i < categories.length; i++) { 
				category = categories[i];
				//console.log(category);
				// render collection view with appropriate category variable
				$(this.el).append(this.template({'category':category}));
				// assign comtainer for models to a jQuery object
				$filters = this.$(".filters-list:last");
				// loop through each model in the collection
				this.collection.each(function(filter) {
					// only render filters from this category

					if (filter.get('category') == category) {
						// console.log(filter.get('category'));
						var view = new FilterSingleView({
							model: filter,
							collection: collection
						});
						$filters.append(view.render().el);
					}
				});
			}
			return this;
		}
	});


});



