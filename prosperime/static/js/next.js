
$(function(){

	//--------------//
	// ** Models ** //
	//--------------//
	window.IndustryChange = Backbone.Model.extend({
		// nothing... is this even needed?
	});



	//-------------------//
	// ** Collections ** //
	//-------------------//
	window.IndustryChanges = Backbone.Collection.extend({

		urlRoot: '/next/',
		model: IndustryChange, 

		initialize: function() {
			this._meta = {}
		},

		url: function() {	
			url = this.urlRoot
			if (this._meta['q1']) url = this.urlRoot + this._meta['q1']		
			if (this._meta['q2']) url += '&' + this._meta['q2']
			return url
		},

	});

	
	// Instantiate Collections
	window.changes = new IndustryChanges;

	//-------------//
	// ** Views ** //
	//-------------//


	/* * * Header View * * */
	window.HeaderView = Backbone.View.extend ({

		el: $('#header-container'),
		template: _.template($('#header-template').html()),

		events: {
		},

		initialize: function() {
			_.bindAll(this,'render', 'remove');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);
		},

		render: function() {
			this.$el.empty()
			var collection = this.collection // important! (context)
			var model = collection.models[0]
			this.$el.append(this.template({
				'industries':model.get('related_industries'),
				'current':model.get('start_name'),
			}))

			return this;
		},

		remove: function() {
			$(this.el).empty().detach()
			return this
		},
	});

	/* * * Filters View * * */
	window.FiltersView = Backbone.View.extend({
		el: $('#search-filters-container'),
		template: _.template($('#search-filters-template').html()),

		events: {
			'click input.search-filters':'checkboxSelected',

		},

		initialize: function() {
			_.bindAll(this,'render', 'checkboxSelected');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);

			/* Filters Constants */
			// this.lvl1filters = ['Most Common', 'Red Herring', 'My Network', 'Prosperime Community'] 
			this.lvl1filters = ['Most Common']
			this.lvl2filters = ['Entity']
		},

		render: function() {
			console.log('2')
			this.$el.empty()
			var level = this.collection.models[0].get('lvl')
			if (level == 1) var filters = this.lvl1filters
			else var filters = this.lvl2filters
			this.$el.append(this.template({'filters':filters}))

			this.collection.models[0].set({'ordering':'decreasing'})
			
		},

		checkboxSelected: function() {
			// console.log(this.collection.models[0].get('transitions'))
			// this.collection.models[0].set({'ordering':'increasing'})
			// var model = this.collection.models[0]
			// this.collection.reset(model)
		},
	});



	/* * * 1 * * */
	window.Lvl1View = Backbone.View.extend ({

		el: $('#search-results-container'),
		template: _.template($('#lvl1-template').html()),

		events: {
			'mouseenter #search-results-table tbody tr': 'tableOver',
			'mouseleave #search-results-table tbody tr': 'tableOut',
			'click #search-results-table tbody tr': 'changeClicked',
		},

		initialize: function() {
			_.bindAll(this,'render', 'remove', 'tableOver', 'tableOut', 'changeClicked');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);
		},

		render: function() {
			console.log('render')
			this.$el.empty()
			var collection = this.collection // important! (context)
			var model = collection.models[0]

			this.$el.append(this.template({
				'start_id':model.get('start_id'),
				'start_name':model.get('start_name'),
				'total_people':model.get('total_people'),
				'transitions':model.get('transitions'),
				'ordering':model.get('ordering'),
			}))

			$('#industry-header').html(model.get('start_name'))

			return this;
		},


		tableOver: function(ev) {
			$(ev.currentTarget).toggleClass('info')
		},

		tableOut: function(ev) {
			$(ev.currentTarget).toggleClass('info')
		},

		changeClicked: function(ev) {
			var row_id =  $(ev.currentTarget).attr('id')
			var from = row_id.split('-')[0]
			var to = row_id.split('-')[1]
			// this.collection._meta['q1'] = '#?i1='+from
			// this.collection._meta['q2'] = 'i2='+to
			// var url = this.collection.url()
			var url = '?i1='+from+'&i2='+to
			console.log(url)
			App.navigate(url, {trigger:true})

		},

	});

	/* * * 2 * * */
	window.Lvl2View = Backbone.View.extend ({

		el: $('#search-results-container'),
		template: _.template($('#lvl2-template').html()),

		events: {
			'mouseenter #search-results-table tbody tr': 'tableOver',
			'mouseleave #search-results-table tbody tr': 'tableOut',
			// 'click #search-results-table tbody tr': 'goToProfile',
			'click span.previous-search':'goBack',
		},

		initialize: function() {
			_.bindAll(this,'render', 'remove', 'tableOver', 'tableOut', 'goToProfile', 'goBack');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);
		},

		render: function() {
			this.$el.empty()
			var collection = this.collection // important! (context)
			console.log(collection)

			var model = collection.models[0]

			this.$el.append(this.template({
				'start_id':model.get('start_id'),
				'start_name':model.get('start_name'),
				'end_id':model.get('end_id'),
				'end_name':model.get('end_name'),
				'total_people':model.get('total_people'),
				'people':model.get('people'),
			}))

			$('#industry-header').html(model.get('start_name'))

			return this;
		},

		tableOver: function(ev) {
			$(ev.currentTarget).toggleClass('info')
		},

		tableOut: function(ev) {
			$(ev.currentTarget).toggleClass('info')
		},

		goToProfile: function(ev) {
			var row_id =  $(ev.currentTarget).attr('id')
			window.location = '/profile/' + row_id + '/'
		},

		// Returns to lvl1 search by manipulating url
		goBack: function(ev) {
			var current = window.location.toString()
			App.navigate(current.substring(current.indexOf('?'), current.indexOf('&')), {trigger:true})
		},

	});


	//---------------//
	// ** Routers ** //
	//---------------//
	window.NextRouter = Backbone.Router.extend({
		routes: {
			'':'empty',
			':query&:query':'doubleQuery',
			':query':'singleQuery',
		},

		initialize: function() {
			this.changes = window.changes;
		},

		empty: function() {
			console.log('empty search')
		},

		singleQuery: function(query) {
			console.log('single query: ' + query)
			this.filterView = new FiltersView({collection:this.changes})
			this.headerview = new HeaderView({collection:this.changes})
			this.lvl1view = new Lvl1View({collection:this.changes})
			this.changes._meta['q1'] = query
			this.changes._meta['q2'] = null
			this.changes.fetch()

		},

		doubleQuery: function(q1, q2) {
			console.log('double query: ' + q1 + ' ' + q2)
			this.filterView = new FiltersView({collection:this.changes})
			this.lvl2view = new Lvl2View({collection:this.changes})
			this.changes._meta['q1'] = q1
			this.changes._meta['q2'] = q2
			this.changes.fetch()

		},

		
		
	});


	window.App = new NextRouter();
	
	// Eventually, change urls for pushState
	// window.App = new SavedPathRouter({pushState:true});
	Backbone.history.start();
});



