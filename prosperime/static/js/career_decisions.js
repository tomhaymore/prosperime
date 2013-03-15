
$(function(){

	//--------------//
	// ** Models ** //
	//--------------//

	window.Decision = Backbone.Model.extend({
		// None
	});


	//-------------------//
	// ** Collections ** //
	//-------------------//
	window.Decisions = Backbone.Collection.extend({

		model:Decision,

		initialize: function() {
			this._meta = {};
		},

		url: function() {

			if (this._meta['query']) {
				console.log('in decisions url, query: ' + this._meta['query'])
				return '/decisions/' + this._meta['query']
			} else {
				console.log('in decisions url, no query')
				return '/decisions/'
			}
		},

		meta: function(prop, value) {
			if (value === undefined) return this._meta[prop];
			else this._meta[prop] = value;
		},
	})


	// Instantiate Collections
	window.decisions = new Decisions;

	//-------------//
	// ** Views ** //
	//-------------//
	// View: PathSingleView
	// window.PathSingleView = Backbone.View.extend({

	// 	tagName: "li",
	// 	template:_.template($('#path-single-template').html()),
	// 	// template:_.template($('#path-single-template-clayton').html()),

	// 	events: {
	// 		"click a.path-name-link" : "renderViz",
	// 	},

	// 	initialize: function() {
	// 		this.model.on('change',this.render,this);	
	// 	},

	// 	render: function() {
	// 		// console.log('path single view: ' + this.model.toJSON())

	// 		var renderedContent = this.template(this.model.toJSON());
	// 		// console.log('here')
	// 		$(this.el).html(renderedContent);
	// 		return this;
	// 	},

	// 	renderViz: function() {
	// 		var pathURL = "/path/" + this.model.id;
	// 		// var renderedPath = pathTemplate(this.model.toJSON());
	// 		// $(this.el).find("div.path-viz-long").html(renderedPath);
	// 		_gaq.push(['_trackEvent','Search','Show Path',this.model.id])
	// 		$(this.el).find("div.path-viz-long").load(pathURL);
	// 		$(this.el).find("div.path-viz-short").toggle();
	// 		$(this.el).find("div.path-viz-long").toggle();
	// 	},

	// 	// WHERE DOES THIS GET CALLED? 
	// 	togglePath: function() {
	// 		console.log('trying to toggle');
	// 		console.log($(this.el));
	// 		$(this.el).find("div.path-viz-short").toggle();
	// 		$(this.el).find("div.path-viz-long").toggle();
	// 	}
	// });

	// View: OrgListView
	window.DecisionListView = Backbone.View.extend({
		
		el: $('#search-results-list'),
		tag: "div",
		template: _.template($('#decisions-list-template').html()),

		events: {
			'click #relevant-careers-checkbox':'relevantCareers',
			'click #positions-of-interest-checkbox':'positionsOfInterest',
			'click #highest-rated-checkbox':'highestRated',
			'click #company-checkbox':'byCompany',
			'click #most-recent-checkbox':'mostRecent',
		},

		initialize: function() {
			_.bindAll(this,'render', 'relevantCareers', 'positionsOfInterest', 'highestRated', 'byCompany', 'mostRecent');
			this.collection.bind('reset',this.render);
		},

		render: function() {
			console.log(this.collection)
			this.$el.append(this.template({}))


		// 	console.log('rendering orglist view')
		// 	var $orgs,
		// 		collection = this.collection;

		// 	$(this.el).html(this.template({}));
		// 	$orgs = this.$(".org-list");
		// 	this.collection.each(function(org) {
		// 		var view = new OrgSingleView({
		// 			model: org,
		// 			collection: collection
		// 		});
		// 		$orgs.append(view.render().el);
		// 	});
		// 	return this;
		// }
		},

		relevantCareers: function() {
			console.log('relevant careers selected')
			this.collection.meta('query', '?term=relevantCareers')
			$('#career-decision-wrapper').remove() // ghetto
			this.collection.fetch()
		},

		positionsOfInterest: function() {
			console.log('p.o.i selected')
			this.collection.meta('query', '?term=positionsOfInterest')
			$('#career-decision-wrapper').remove() // ghetto
			this.collection.fetch()
		},

		highestRated: function() {
			console.log('higest rated selected')
			this.collection.meta('query', '?term=highestRated')
			$('#career-decision-wrapper').remove() // ghetto
			this.collection.fetch()
		},

		byCompany: function() {
			console.log('by company selected')
			this.collection.meta('query', '?term=byCompany')
			$('#career-decision-wrapper').remove() //ghetto 
			this.collection.fetch()	
		},

		mostRecent: function() {
			console.log('most recent selected')
			this.collection.meta('query', null) // DEFAULT!
			$('#career-decision-wrapper').remove() // ghetto
			this.collection.fetch()
		},

	});

	
	//---------------//
	// ** Routers ** //
	//---------------//
	window.DecisionRouter = Backbone.Router.extend({

		routes: {
			"" : "emptySearch",
			"paths/" : "emptyPathSearch",
			"paths/:query" : "pathSearch",
		},

		initialize: function() {
			this.decisions = window.decisions;
			this.decisionListView = new DecisionListView({ collection: this.decisions })
		},

		emptySearch: function() {
			console.log('empty search')
			this.decisions.query = null
			this.decisions.fetch()
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



	});

	window.App = new DecisionRouter;
	Backbone.history.start();
});



