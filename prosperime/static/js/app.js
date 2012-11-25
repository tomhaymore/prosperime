
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

		initialize: function() {
			// initialize array of meta data
			this._meta = {};
		}

		model:Filter,
		url: function() {
			if (this._meta['query'] === undefined) {
				return '/filters';
			} else {
				return '/filters?'+this._meta['query'];
			}
		},

		meta: function(prop, value) {
			if (value === undefined) {
				// if value is empty, return property of key
				return this._meta[prop];
			} else {
				// if both key and value exist, set value of key
				this._meta[prop] = value;
			}
		}
	})

	// Orgs: collection of orgs

	window.Orgs = Backbone.Collection.extend({

		initialize: function() {
			// initialize array of meta data
			this._meta = {};
		},

		model: Org,
		url: function() {
			if (this._meta['query'] === undefined) {
				return '/companies';
			} else {
				return '/companies?'+this._meta['query'];
			}
		}

		meta: function(prop, value) {
			if (value === undefined) {
				// if value is empty, return property of key
				return this._meta[prop];
			} else {
				// if both key and value exist, set value of key
				this._meta[prop] = value;
			}
		}

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
			// create dict of all selected filters
			var selectedFilters = {};

			var locationFilters = $("input[name='Location-filters']:checked").map(function(filter) { return this.value });
			var sectorFilters = $("input[name='Sector-filters']:checked").map(function(filter) { return this.value });
			var sizeFilters = $("input[name='Size-filters']:checked").map(function(filter) { return this.value });
			var stageFilters = $("input[name='Stage-filters']:checked").map(function(filter) { return this.value });
			
			// construct URL

			selectedFilters.location = locationFilters;
			selectedFilters.sector = sectorFilters;
			selectedFilters.size = sizeFilters;
			selectedFilters.stage = stageFilters;

			filterUrl = "/search/?" + generateUrl(selectedFilters);

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

	window.App = Backbone.Router.extend({

		routes: {
			"search:query" : "search"
		},

		search: function(query) {
			this.orgs.meta('query',query);
			this.filters.meta('query',query);
			this.orgs.fetch();
			this.filters.fetch();
		}

	});

	// Custome functions

	function generateUrl(params) {
		var fullUrl = '';

		for (var key in params) {
			if (params.hasOwnProperty(key)) {
				for (i=0;i<=key.length;i++) {
					if (i == 0) {
						fullUrl += key + "='" + encodeURIComponent(key[i]) + "'";
					} else {
						fullUrl += "+" + encodeURIComponent(key[i]);
					}
				}
			}
		}
		return fullUrl;
	}


});



