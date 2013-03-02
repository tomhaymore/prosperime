
// kick off app once DOM is ready

$(function(){


	// window.archtype = Raphael($("#arc-container"), 150, 150);

	// archtype.customAttributes.arc = function (xloc, yloc, value, total, R) {
	//     var alpha = 360 / total * value,
	//         a = (90 - alpha) * Math.PI / 180,
	//         x = xloc + R * Math.cos(a),
	//         y = yloc - R * Math.sin(a),
	//         path;
	//     if (total == value) {
	//         path = [
	//             ["M", xloc, yloc - R],
	//             ["A", R, R, 0, 1, 1, xloc - 0.01, yloc - R]
	//         ];
	//     } else {
	//         path = [
	//             ["M", xloc, yloc - R],
	//             ["A", R, R, 0, +(alpha > 180), 1, x, y]
	//         ];
	//     }
	//     return {
	//         path: path
	//     };
	// };
	// Models


	//--------------//
	// ** Models ** //
	//--------------//

	// Filter: dynamically loaded search param
	window.Filter = Backbone.Model.extend({
		// none
	});

	// Org: search result for for organizations
	window.Org = Backbone.Model.extend({
		// none
	});

	// Path: search result view for career paths
	window.Path = Backbone.Model.extend({
		// none
	});



	//-------------------//
	// ** Collections ** //
	//-------------------//
	// Filters: collection of filters
	window.Filters = Backbone.Collection.extend({

		initialize: function() {
			// initialize array of meta data
			this._meta = {
				'view':'paths'
			};
		},

		model:Filter,
		url: function() {
			// set base path to either company or path filters
			var init_path;
			if (this._meta['view'] == 'companies') {
				init_path = '/filters/';
			} else if (this._meta['view'] == 'paths') {
				init_path = '/pathfilters/';
			} else if (this._meta['view'] == 'careers') {
				init_path = '/careerfilters/';
			} else {
				init_path = '/pathfilters/';
			}

			// add queries if they exist
			if (this._meta['query'] === undefined) {
				return init_path
			} else {
				path = init_path + this._meta['query'];
				return path;
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
				return '/companies'+this._meta['query'];
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
	});

	// Paths: collection of paths
	window.Paths = Backbone.Collection.extend({
		
		initialize: function() {
			// initialize array of meta data
			this._meta = {};
		},

		model: Path,

		url: function() {
			if (this._meta['query'] === undefined) {
				return '/paths';
			} else {
				return '/paths'+this._meta['query'];
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
	});

	

	// Instantiate Collections
	window.orgs = new Orgs;
	window.filters = new Filters;
	window.paths = new Paths;

	//-------------//
	// ** Views ** //
	//-------------//

	// View: PathSingleView
	window.PathSingleView = Backbone.View.extend({

		tagName: "li",
		template:_.template($('#path-single-template').html()),
		// template:_.template($('#path-single-template-clayton').html()),

		events: {
			"click a.path-name-link" : "renderViz",
		},

		initialize: function() {
			this.model.on('change',this.render,this);	
		},

		render: function() {
			console.log('path single view: ' + this.model.toJSON())

			var renderedContent = this.template(this.model.toJSON());
			console.log('here')
			$(this.el).html(renderedContent);
			return this;
		},

		renderViz: function() {
			var pathURL = "/path/" + this.model.id;
			// var renderedPath = pathTemplate(this.model.toJSON());
			// $(this.el).find("div.path-viz-long").html(renderedPath);
			_gaq.push(['_trackEvent','Search','Show Path',this.model.id])
			$(this.el).find("div.path-viz-long").load(pathURL);
			$(this.el).find("div.path-viz-short").toggle();
			$(this.el).find("div.path-viz-long").toggle();
		},

		// WHERE DOES THIS GET CALLED? 
		togglePath: function() {
			console.log('trying to toggle');
			console.log($(this.el));
			$(this.el).find("div.path-viz-short").toggle();
			$(this.el).find("div.path-viz-long").toggle();
		}
	});

	// View: OrgSingleView
	window.OrgSingleView = Backbone.View.extend({

		template:_.template($('#org-single-template').html()),

		initialize: function() {
			this.model.on('change',this.render,this);
			//this.template = _.template($('#org-single-template').html())
		},

		render: function() {
			console.log('org single view')
			// var renderedContent = $(this.el).html(this.template(this.model.toJSON()));
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		}

	});

	// View: PathListview
	window.PathListView = Backbone.View.extend({

		el: $('#search-results-list'),
		tag: 'div',
		template: _.template($('#path-list-template').html()),

		initialize: function() {
			_.bindAll(this,'render');
			this.collection.bind('reset',this.render);
		},

		render: function() {
			console.log('path list view')
			var $paths,
				collection = this.collection;

			$(this.el).html(this.template({}));
			$paths = this.$(".path-list");
			this.collection.each(function(path) {
				var view = new PathSingleView({
					model: path,
					collection: collection
				});
				$paths.append(view.render().el);
			});
			return this;
		}
	});

	// View: FilterSingleView
	window.FilterSingleView = Backbone.View.extend ({
		tagName: 'li',
		template: _.template($("#search-filters-template").html()),

		initialize: function() {
			this.model.on('change',this.render,this);
		},

		render: function() {
			// console.log('filter single view')
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		},

		events: {
			"click input.input-search-filter" : "filter"
		},

		filter: function() {
			// track with google
			_gaq.push(['_trackEvent','Search','Filter',this.model.value])

			// create dict of all selected filters
			var selectedFilters = {};

			var locationFilters = $("input[name='Location-filters']:checked").map(function(filter) { return this.value });
			var sectorFilters = $("input[name='Sector-filters']:checked").map(function(filter) { return this.value });
			var sizeFilters = $("input[name='Size-filters']:checked").map(function(filter) { return this.value });
			var stageFilters = $("input[name='Stage-filters']:checked").map(function(filter) { return this.value });
			var positionFilters = $("input[name='Positions-filters']:checked").map(function(filter) { return this.value });

			// construct URL
			if (locationFilters.length > 0 ) {
				selectedFilters.location = locationFilters;
			}
			if (sectorFilters.length > 0) {
				selectedFilters.sector = sectorFilters;				
			}
			if (sizeFilters.length > 0) {
				selectedFilters.size = sizeFilters;
			}
			if (stageFilters.length > 0) {
				selectedFilters.stage = stageFilters;
			}
			if (positionFilters.length > 0) {
				selectedFilters.position = positionFilters;
			}
			
			// set initial URL path

			// var init_path = window.filters._meta['view'];
			var init_path = this.collection._meta['view'];

			if (jQuery.isEmptyObject(selectedFilters)) {
				// filterUrl = '/search/';
				filterUrl = init_path + "/";
			} else {
				filterUrl = init_path + "/?" + generateUrl(selectedFilters);
			}

			// trigger router to navigate
			// console.log(filterUrl);
			//Backbone.history.navigate(filterUrl,{trigger:true});
			App.navigate(filterUrl,{trigger:true});
		}
	});

	// View: OrgListView
	window.OrgListView = Backbone.View.extend({
		
		//el: $('#org-list'),
		el: $('#search-results-list'),
		tag: "div",
		template: _.template($('#org-list-template').html()),

		initialize: function() {
			_.bindAll(this,'render');
			this.collection.bind('reset',this.render);
		},

		render: function() {
			console.log('rendering orglist view')
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

	// View: FilterListView
	window.FilterListView = Backbone.View.extend ({

		el: $("#search-filters-container"),
		tagName: 'div',
		template: _.template($("#search-module-template").html()),

		initialize: function() {
			_.bindAll(this,'render');
			this.collection.bind('reset',this.render);
		},

		events: {
			"click a.search-control-close" : "minimize",
			"click a.search-control-open" : "maximize"
		},

		render: function() {
			var $filters,
				filterCategories,
				collection = this.collection;

			$(this.el).empty();
			$(this.el).append(_.template($("#search-header-template").html()));
			
			// pull out unique list of categories
			categories = filters.map(function(model) { return model.get('category'); });
			categories = _.uniq(categories);
			for (var i = 0; i < categories.length; i++) { 
				category = categories[i];
				// console.log(category);

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
		},

		// uncheck all filters
		uncheckAll: function() {
			$filters = this.$(".input-search-filter");
			$filters.prop('checked',false);
		},

		minimize: function() {
			$("div#sidebar-column").removeClass("max-filters").addClass("min-filters");
			$("div#middle-column").removeClass("min-results").addClass("max-results");
			$("div.search-form-module").hide();
			$("a.search-control-close").hide();
			$("a.search-control-open").show();
		},

		maximize: function() {
			$("div#sidebar-column").removeClass("min-filters").addClass("max-filters");
			$("div#middle-column").removeClass("max-results").addClass("min-results");
			$("div.search-form-module").show();
			$("a.search-control-close").show();
			$("a.search-control-open").hide();
		}

	});

	
	// window.arcMeta = {
	// 	'peopleArc':null, 
	// 	'orgsArc':null, 
	// 	'positionsArc': null,
	// 	'usersCount': null,
	// 	'orgsCount': null,
	// 	'positionsCount': null,
	// 	'fullUsersCount': null,
	// 	'fullOrgsCount': null,
	// 	'fullPositionsCount': null,
	// };

	window.CareersView = Backbone.View.extend({

		// var peopleArc, orgsArc, positionsArc, usersCount,orgsCount,positionsCount,fullUsersCount,fullOrgsCount,fullPositionsCount,
		// initialize array of meta data

		el: $("#search-results-list"),

		url: function() {
			if (this._meta['query'] === undefined) {
				return '/careers';
			} else {
				return '/careers'+this._meta['query'];
			}
		},

		initialize: function() {
			_.bindAll(this,'render');
			this._meta = {};
			// window.archtype = Raphael("arc-container", 150, 150);
			

			// archtype.customAttributes.arc = function (xloc, yloc, value, total, R) {
			//     var alpha = 360 / total * value,
			//         a = (90 - alpha) * Math.PI / 180,
			//         x = xloc + R * Math.cos(a),
			//         y = yloc - R * Math.sin(a),
			//         path;
			//     if (total == value) {
			//         path = [
			//             ["M", xloc, yloc - R],
			//             ["A", R, R, 0, 1, 1, xloc - 0.01, yloc - R]
			//         ];
			//     } else {
			//         path = [
			//             ["M", xloc, yloc - R],
			//             ["A", R, R, 0, +(alpha > 180), 1, x, y]
			//         ];
			//     }
			//     return {
			//         path: path
			//     };
			// };
		},

		events: {
			"hover .careers-single"		: "fadeIn",
			"click .careers-single"		: "expandCareer",
			// "click .careers-single"		: "drawArc"

		},

		render: function() {
			console.log('attempting to render careers view')
			$(this.el).empty();
			
			var _this = this;

			$.get(_this.url(), function(data) {
				
				fullCareers = $(data);
				$("div#search-results-list").html(fullCareers[0]);
				
				$("div#search-right-sidebar").empty().html(fullCareers[2]);
				
				// $("div#search-right-sidebar").append(fullCareers[4]);

				var thisContainer = fullCareers.find("#careers-header");

				// arcMeta.fullUsersCount = thisContainer.data('userscount');
				// arcMeta.fullPositionsCount = thisContainer.data('positionscount');
				// arcMeta.fullOrgsCount = thisContainer.data('orgscount');

				_this.meta('fullUsersCount',thisContainer.data('userscount'));
				_this.meta('fullPositionsCount',thisContainer.data('positionscount'));
				_this.meta('fullOrgsCount',thisContainer.data('orgscount'));


			});	


			// arcMeta.peopleArc = archtype.path().attr({
			//     "stroke": "#f00",
			//     "stroke-width": 10,
			//     arc: [75, 60, 100, 100, 30]
			// });

			// arcMeta.orgsArc = archtype.path().attr({
			// 	"stroke": "#8c8c8c",
			// 	"stroke-width": 10,
			// 	arc: [75, 60,100,100,40]
			// })

			// arcMeta.positionsArc = archtype.path().attr({
			// 	"stroke": "#8c8c8c",
			// 	"stroke-width": 10,
			// 	arc: [75, 60,100,100,50]
			// })


			return this;
		},

		fadeIn: function(ev) {
			$("img.careers-user-thumbnail").removeClass("careers-user-thumbnail-expose");

			var imgs = ($(ev.currentTarget).find('img'));
			$(imgs).toggleClass("careers-user-thumbnail-expose");

			var stats = ($(ev.currentTarget).find('div.careers-stats'));
			$(stats).toggleClass("careers-stats-expose");
			
		},

		drawArc: function(ev) {
			this.expandCareer(ev);
			var thisCareer = $(ev.currentTarget);
			// console.log(thisCareer.data());
			usersCount = thisCareer.data('userscount');
			positionsCount = thisCareer.data('positionscount')
			orgsCount = thisCareer.data('orgscount');
			
			// console.log([75,60,usersCount,arcMeta.fullUsersCount,30]);
			
			arcMeta.peopleArc.attr({arc:[75,60,usersCount,arcMeta.fullUsersCount,30]});
			arcMeta.orgsArc.attr({arc:[75,60,orgsCount,arcMeta.fullOrgsCount,40]});
			arcMeta.positionsArc.attr({arc:[75,60,positionsCount,arcMeta.fullPositionsCount,50]});

	
		},

		expandCareer: function(ev) {
			
			var currentTarget = $(ev.currentTarget);
			
			usersCount = currentTarget.data('userscount');
			positionsCount = currentTarget.data('positionscount')
			orgsCount = currentTarget.data('orgscount');

			var careerInfo = currentTarget.find(".careers-info");

			if (careerInfo.hasClass('hidden')) {
				$(".careers-info").addClass('hidden');
				
				careerInfo.toggleClass('hidden');

				this.updateStats([usersCount,positionsCount,orgsCount])
			} else {
				$(".careers-info").addClass('hidden');

				this.updateStats([this.meta('fullUsersCount'),this.meta('fullPositionsCount'),this.meta('fullOrgsCount')])
			}
			
		},

		updateStats: function(stats) {

			$(".careers-stats-people").html(stats[0]);
			$(".careers-stats-positions").html(stats[1]);
			$(".careers-stats-orgs").html(stats[2]);
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

	});


	//---------------//
	// ** Routers ** //
	//---------------//
	window.SearchRouter = Backbone.Router.extend({

		routes: {
			"" : "emptySearch",
			"paths/" : "emptyPathSearch",
			"paths/:query" : "pathSearch",
			"companies/" : "emptyCompanySearch",
			"companies/:query" : "companySearch",
			"careers/" : "emptyCareerSearch",
			"careers/:query" : "careerSearch",
		},

		initialize: function() {

			// set collections
			this.orgs = window.orgs;
			this.filters = window.filters;
			this.paths = window.paths;

			// set views
			// show paths and path filters by default
			this.orgsView = new OrgListView({ collection: this.orgs});
			this.filtersView = new FilterListView({ collection: this.filters});
			this.pathsView = new PathListView({ collection: this.paths});
			this.careersView = new CareersView();
		},

		emptyCareerSearch: function() {
			console.log("empty careers search");
			this.filters.meta('view','careers');
			this.filters.meta('query','');
			this.filters.fetch()
			this.careersView.meta('query','');
			this.careersView.render();
		},

		careerSearch: function(query) {
			console.log(query);
			this.filters.meta('view','careers');
			
			// test for empty search string, make sure to uncheck all filters
			if (query === undefined) {
				this.filtersView.uncheckAll();
				this.careersView.meta('query','');
				this.filters.meta('query','');
			} else {
				this.careersView.meta('query',query);
				this.filters.meta('query',query);	
			}
			this.careersView.render();
			this.filters.fetch();
		},

		emptySearch: function() {
			// this.filters.meta('view','careers');
			this.filters.meta('query','');
			this.filters.fetch()
			//this.careersView.render();

			// // this.orgs.fetch();
			this.paths.fetch();
		},

		emptyPathSearch: function() {
			console.log('empty path search');
			// reset to career paths as default
			this.filters.meta('view','paths');
			this.filters.meta('query','');
			this.paths.meta('query','');
			// fetch filters
			this.filters.fetch();
			// fetch paths
			this.paths.fetch();
		},

		pathSearch: function(query) {
			console.log("searching paths");
			console.log(query);
			// set to path view
			this.filters.meta('view','paths');
			// test for empty search string, make sure to uncheck all filters
			if (query === undefined) {
				this.filtersView.uncheckAll();
				this.paths.meta('query',null);
				this.filters.meta('query',null);
			} else {
				this.paths.meta('query',query);
				this.filters.meta('query',query);	
			}
			this.paths.fetch();
			this.filters.fetch();
		},

		emptyCompanySearch: function() {
			console.log('empty company search');
			// reset to company search
			this.filters.meta('view','companies');
			this.filters.meta('query','');
			// fetch filters
			this.filters.fetch();
			// fetch orgs
			this.orgs.fetch();
		},

		companySearch: function(query) {
			console.log("searching companies");
			console.log(query);
			// set to path view
			this.filters.meta('view','companies');
			// test for empty search string, make sure to uncheck all filters
			if (query === undefined) {
				this.filtersView.uncheckAll();
				this.orgs.meta('query',null);
				this.filters.meta('query',null);
			} else {
				this.orgs.meta('query',query);
				this.filters.meta('query',query);	
			}
			this.orgs.fetch();
			this.filters.fetch();
		},
	});


	// Custom functions
	function generateUrl(params) {
		var fullUrl = '';
		c = 0;
		for (var key in params) {
			if (params.hasOwnProperty(key)) {
				for (i=0;i<=params[key].length;i++) {
					if(params[key][i] === undefined) {
						continue;
					} else {
						if (i == 0 && c == 0) {
							fullUrl += key + "=" + encodeURIComponent(params[key][i]);
						} else if (i == 0) {
							fullUrl += "&" + key + "=" + encodeURIComponent(params[key][i]);
						 } // else {
						// 	fullUrl += "+'" + encodeURIComponent(params[key][i]) + "'";
						// }
					}
				}
			}
			c++;
		}
		return fullUrl;
	}

	window.App = new SearchRouter;
	Backbone.history.start();
});



