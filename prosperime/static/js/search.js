$(function(){
	
	//--------------//
	// ** Models ** //
	//--------------//
	window.Question = Backbone.Model.extend({ });

	//-------------------//
	// ** Collections ** //
	//-------------------//
	window.Questions = Backbone.Collection.extend({

		model:Question,

		initialize:function() {
			// initialize array of meta data
			this._meta = {};
		},

		url:function() {
			path = "/api/conversations/?query=" + this._meta['query'];	
			return path;
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

	window.questions = new Questions;
	//-------------//
	// ** Views ** //
	//-------------//

	// View: PathSingleView
	window.QuestionSingleView = Backbone.View.extend({

		template:_.template($("#question-template").html()),

		events: {
		},

		initialize: function() {
			this.model.on('change',this.render,this);	
		},

		render: function() {
			var renderedContent = this.template(this.model.toJSON());
			$(this.el).html(renderedContent);
			return this;
		},
	});


	// View: PathListview
	window.QuestionListView = Backbone.View.extend({

		el: $('#questions-list-container'),
		tag: "div",
		template: _.template($('#question-list-template').html()),

		initialize: function() {
			_.bindAll(this,'render', 'showNoResults');
			this.collection.bind('reset',this.render);
		},

		render: function() {
			// if no results, show 
			if (this.collection.length == 0) {
				this.showNoResults(this.collection._meta["query"]);
				return false;
			}
			// Don't pass anything to this template
			$(this.el).html(this.template({}));
			// Declare local collection variable outside (scoping)
			var collection = this.collection;

			// Declare local DOM container outside (scoping)
			var $questions = this.$el;

			// Delegate Question rendering to sub-view
			this.collection.each(function(question) {
				var view = new QuestionSingleView({
					model: question,
					collection: collection // needed?
				});
				$questions.append(view.render().el);
			});
			return this;
		},

		showNoResults: function(query) {
			var msg = _.template($("#no-results-template").html())
			$("#center-column").append(msg({'query':query}))
		},	
	});


	//---------------//
	// ** Routers ** //
	//---------------//
	window.ConversationRouter = Backbone.Router.extend({

		routes: {
			"" : "default",
			":query" : "search"
		},

		initialize: function() {

			this.questions = window.questions;
			this.questionsView = new QuestionListView({collection:this.questions});
		},

		default: function() {
			console.log('Default view');
			this.questions.meta("query","");
			this.questions.fetch();
			this.questionsView.render();
		},

		search: function(query) {
			console.log("Search view:", query);

			if (query == "undefined") {
				this.questions.meta("query","")
			} else {
				this.questions.meta("query",query)
				console.log(this.questions.url());
			}
			this.questions.fetch();
			this.questionsView.render();
		}

	});

	window.App = new ConversationRouter;
	Backbone.history.start();

});


