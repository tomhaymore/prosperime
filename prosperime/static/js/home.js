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
			if (this.meta("tagName") != "undefined") {
				var path = "/api/conversations/?tag=" + this._meta['tagName'];
			} else {
				var path = "/api/conversations/?query=" + this._meta['query'];	
			}
			
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

		el: $('#questions-list'),
		tag: "div",
		template: _.template($('#question-list-template').html()),

		initialize: function() {
			_.bindAll(this,'render');
			this.collection.bind('reset',this.render);
		},

		render: function() {
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
		}
	});


	//---------------//
	// ** Routers ** //
	//---------------//
	window.ConvoRouter = Backbone.Router.extend({

		routes: {
			"" : "default",
			"search/:query" : "search",
			"tags/:tagName" : "tags"
		},

		initialize: function() {

			$("input#search-conversations-input").typeahead({
		    	name:'conversations',
		    	remote:'/api/conversations_autocomplete/?q=%QUERY',
		    	limit: 5
		    });

			// Listen to filter button
			$("#search-conversations-button").on("click", function(ev) {

				// var url = $.param({'query':$("input#search-conversations-input").val()});
				var url = "search/" + encodeURIComponent($("input#search-conversations-input").val())
				window.App.navigate(url, {trigger:true})
			})

			// Set collection, view
			// window.questions = new Questions()
			this.questions = window.questions;
			this.questionsView = new QuestionListView({collection:this.questions});
		},

		default: function() {
			console.log('default');
			this.questions.meta("query","");

			this.questions.fetch();
			this.questionsView.render();
		},

		search: function(query) {
			if (query == "undefined") {
				this.questions.meta("query","")
			} else {
				this.questions.meta("query",query)
			}
			this.questions.fetch();
			this.questionsView.render();
		},

		tags: function(tagName) {
			if (tagName == "undefined") {
				this.questions.meta("tagName","")
			} else {
				this.questions.meta("tagName",tagName)
			}
			this.questions.fetch();
			this.questionsView.render();
		}

	});

	window.App = new ConvoRouter;
	Backbone.history.start();

});


