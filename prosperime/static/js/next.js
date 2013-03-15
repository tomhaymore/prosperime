
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
			_.bindAll(this,'render', 'remove', 'addFilters', 'tableOver', 'tableOut', 'changeClicked');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);
		},

		render: function() {
			this.$el.empty()
			var collection = this.collection // important! (context)

			var level = collection.models[0].get('lvl')
			this.addFilters(level)

			var model = collection.models[0]

			this.$el.append(this.template({
				'start_id':model.get('start_id'),
				'start_name':model.get('start_name'),
				'total_people':model.get('total_people'),
				'transitions':model.get('transitions'),
			}))
			
			$('#industry-header').html(model.get('start_name'))

			// this.collection.each(function(queueItem) {
			// 	var positions = queueItem.attributes['positions']
			// 	collection.num_positions = positions.length
			// 	collection.positions = positions

			// 	if (positions.length > 4) {
			// 		for (var m = 0; m < 4; m++) collection.queue_indices.push(m)
			// 		collection.overflow = true
			// 	} else {
			// 		for (var j = 0; j < positions.length; j++) collection.queue_indices.push(i)
			// 	}

			// 	console.log(positions)
			// 	collection.create_queue_boxes(collection, positions)
			// });

			return this;
		},

		addFilters: function(level) {
			var container = $('#search-filters-container')
			container.empty()
			var template = _.template($('#search-filters-template').html())
			var filters = ['Most Common', 'Red Herring', 'My Network', 'Prosperime Community'] 
			console.log(filters)
			container.append(template({'filters':filters}))
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
			console.log('from: ' + from + ' to: ' + to)
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
			_.bindAll(this,'render', 'remove', 'addFilters', 'tableOver', 'tableOut', 'goToProfile', 'goBack');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);
		},

		render: function() {
			this.$el.empty()
			var collection = this.collection // important! (context)
			console.log(collection)

			var level = collection.models[0].get('lvl')
			console.log('level ' + level)
			this.addFilters(level)

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

		addFilters: function(level) {
			var container = $('#search-filters-container')
			container.empty()
			var template = _.template($('#search-filters-template').html())
			var filters = ['Entity']
			container.append(template({filters:filters}))
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
			this.lvl1view = new Lvl1View({collection:this.changes})
			this.changes._meta['q1'] = query
			this.changes._meta['q2'] = null
			this.changes.fetch()

		},

		doubleQuery: function(q1, q2) {
			console.log('double query: ' + q1 + ' ' + q2)
			this.lvl2view = new Lvl2View({collection:this.changes})
			this.changes._meta['q1'] = q1
			this.changes._meta['q2'] = q2
			this.changes.fetch()
			// console.log(this.changes.models[0].attributes)
		},

		
		
	});


	window.App = new NextRouter();
	
	// Eventually, change urls for pushState
	// window.App = new SavedPathRouter({pushState:true});
	Backbone.history.start();
});



