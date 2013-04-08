
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
			"click #save-button":"saveIndustry",
		},

		initialize: function() {
			_.bindAll(this,'render', 'remove', 'saveIndustry');
			this.collection.on('reset',this.render, this);
			this.collection.on('change', this.render, this);
		},

		render: function() {
			this.$el.empty()
			var collection = this.collection // important! (context)
			var model = collection.models[0]

			console.log(model)

			// Check if this is a new search. If so, allow user to 
			// bookmark this industry
			var new_industry = true
			for (var i = 0; i < model.get('related_industries').length; i++) {
				if (model.get('start_id') == model.get('related_industries')[i][0])
					new_industry = false
			};

			if (new_industry) {
				var new_el = "<div id='save-button' class='pull-right inline-block people-box' data-id='" + model.get('start_id') + "'>Save this search</div>"
				$('#lvl1-header-container').append(new_el)

				// Attach click handler to button after added
				var id = model.get('start_id')
				$('#save-button').on("click", function() {
					var id = $(this).data("id")

					// Make sure industry not a duplicate!
					for (var h = 0; h < model.get('related_industries'); h++) {
						if (id == model.get('related_industries')[h][0]) {
							return false;
						}
					}

					// Save Industry
					$.post('/careers/addIndustry/', {
						id:id}, function(response) {
							if (response["result"] == "success") {
								console.log("Success")
								// $('#save-button').fadeIn(100).fadeOut(100).fadeIn(100).fadeOut(100).fadeIn(100)
							} else {
								console.log("Failed to save industry: " + response["errors"])
							}
						}, "json");
					collection.fetch()
					collection.render()
				})
			}

			this.$el.append(this.template({
				'industries':model.get('related_industries'),
				'current':model.get('start_name'),
			}));

			return this;
		},

		remove: function() {
			$(this.el).empty().detach()
			return this
		},

		saveIndustry: function(id) {

			console.log("save: " + id)
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
			'mouseenter #search-results-table-lvl1 tbody tr': 'tableOver',
			'mouseleave #search-results-table-lvl1 tbody tr': 'tableOut',
			'click #search-results-table-lvl1 tbody tr': 'changeClicked',
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
			'mouseenter #search-results-table-lvl2 tbody tr': 'tableOver',
			'mouseleave #search-results-table-lvl2 tbody tr': 'tableOut',
			'click span.previous-search':'goBack',
			'click #search-results-table-lvl2 tbody tr':'goToProfile',
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

			// Now add timelines
			var constants = {
				'paper_w':700,
				'paper_h':100,
				'midline':50,
				'start_offset':0,
				'padding':3,
				'top_text_offset':37,
				'bottom_text_offset':23,
			}

			_.each(model.get('people'), function(value, key) {

				var move = value[1]
				var positions = [{'title':move.start_title, 'org':move.start_entity_name}, {'title':move.end_title, 'org':move.end_entity_name}]
				monospaced_timeline(constants, positions, "content-"+ key)

			});

		


			return this;
		},

		tableOver: function(ev) {
			$(ev.currentTarget).toggleClass('info')
			// $(ev.currentTarget).children(".first-col").children(".flat-button").toggleClass("hide")
		},

		tableOut: function(ev) {
			$(ev.currentTarget).toggleClass('info')
		},

		goToProfile: function(ev) {
			var row_id =  $(ev.currentTarget).attr('id')
			window.location = "/profile/" + row_id + "/"
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
			this.lvl1view = new Lvl1View({collection:this.changes})

			// Keep this call last
			this.headerview = new HeaderView({collection:this.changes})

			this.changes._meta['q1'] = query
			this.changes._meta['q2'] = null
			this.changes.fetch()

		},

		doubleQuery: function(q1, q2) {
			console.log('double query: ' + q1 + ' ' + q2)

			if (q2 == 'undefined') {
				console.log('here')
				App.history.back()
				App.history.back()
				return
			}

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



