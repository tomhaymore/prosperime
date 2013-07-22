
// these pics time out after an hour or so, have to refresh... I just take a random slice of Users
var pics = ['https://prosperme_images.s3.amazonaws.com/pictures/vincent_cannon/vincent_cannon.jpg?Signature=KeDZ%2FlqWB0t8%2FUxXNeBl4DC2kOA%3D&Expires=1374296488&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/patrick_carroll/patrick_carroll.jpg?Signature=4AIoRMaBc817kCJD8vP6HWupKdI%3D&Expires=1374296489&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/melissa_arano/melissa_arano.jpg?Signature=%2FyV1MtbLFeVS%2B4dQigN8FNN0es0%3D&Expires=1374296489&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/amanda_berry/amanda_berry.jpg?Signature=8tXR9fjiOvBU63h%2Bja1lg6AWAb4%3D&Expires=1374296489&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/annie_bezbatchenko/annie_bezbatchenko.jpg?Signature=t0x6LlMvtV%2FP0eDqratHteAzlK4%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/tahira_%28taida%29_adaya/tahira_%28taida%29_adaya.jpg?Signature=u3gvX0D73Mwd1R6G69r5eWjiipM%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/tara_adiseshan/tara_adiseshan.jpg?Signature=vEEImFI99v5xTfSsZAlvbNcfbnQ%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/william_clayton/william_clayton.jpg?Signature=l%2FKgB6FJyhX2JPh3%2FdWtEI5h%2FuE%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/chike_amajoyi/chike_amajoyi.jpg?Signature=MlzTbv01ltEMQKSKkIf0Pz0FZFU%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/emily_cox/emily_cox.jpg?Signature=h%2FchXhR2PMa%2Fe%2BXl%2FfE%2Fzcm1%2By8%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/carly_crandall/carly_crandall.jpg?Signature=%2B220oSemJOCYvchY337vA71afX8%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 '/media/pictures/anon.jpg',
 'https://prosperme_images.s3.amazonaws.com/pictures/yosem_companys/yosem_companys.jpg?Signature=5CsHM5Gj5uOdLn6TTuF5sm4SB5Q%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/christopher_condlin/christopher_condlin.jpg?Signature=aT%2BOixXlfjVbrIB51ZbSfMfsOPQ%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/stan_darger%2C_jr./stan_darger%2C_jr..jpg?Signature=vVzLBf2RxQh%2BeWNlx0FdymtWF9A%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/heather_davidson/heather_davidson.jpg?Signature=ZqJVpiIIjPdi%2Fd3cS6h3UqmEIDE%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/jason_davies%2C_md%2C_phd/jason_davies%2C_md%2C_phd.jpg?Signature=Hgx75rtoxVx%2F8%2BLSVii59NH7Uz8%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/miles_davis/miles_davis.jpg?Signature=1t1uxEhhbV5J3%2BPqo8isTMoEB7s%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/logan_deans/logan_deans.jpg?Signature=h4ptL01yPLRfMJKqkjOZ3qKOko4%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/aidan_dunn/aidan_dunn.jpg?Signature=UfDfDOift0K%2BlupZgxttiXzxoh0%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/marie_dutton/marie_dutton.jpg?Signature=oJwClP0MUy5BfuTI5j8f3cBkA1g%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/greta_dyer/greta_dyer.jpg?Signature=Q1FIjRTkMFQ8kbXdPRtpzaU9daI%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/michael_elgarico/michael_elgarico.jpg?Signature=ZFLWLg4j%2BDimBR%2FmyDIwhr3lbCE%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/solomon_k._enos/solomon_k._enos.jpg?Signature=f4hc6Io47vS473MCm0I8LKfeJ2Q%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82',
 'https://prosperme_images.s3.amazonaws.com/pictures/mike_field/mike_field.jpg?Signature=hWLYA3YPgBS%2FZ%2BXAXZYrDPGsOKE%3D&Expires=1374296490&AWSAccessKeyId=0MK6PWWNA8B6Q3FCZT82']

var titles = [
 	"What can I do with my Math degree?",
 	"What is the biggest professional mistake you've ever made?",
 	"Are there any options out there for STS majors?",
 	"What is like to work in Management Consulting from Stanford?",
 	"What are the most important classes that you ever took? Why?",
 	"What is the best way to create a great relationship with an SAM mentor?",
 	"How should I prepare for an engineering interview @Apple?",
 	"Any Music alums out there?",
 	"What firms are notorious for overselling first-years?"
]

var tags = [
	{"title":"Great Hours", "id":7, "type":"Good"},
	{"title":"What Perks", "id":7, "type":"Bad"},
	{"title":"Crazy Hours", "id":7, "type":"Bad"},
	{"title":"Strict Culture", "id":7, "type":"Eh"},
	{"title":"Great Pay", "id":7, "type":"Good"},
	{"title":"Great Cause", "id":7, "type":"Good"},
	{"title":"Just a Paycheck", "id":7, "type":"Bad"},
]

var bodies = [
	"Not the greatest experience, to be brutally honest. While no one can argue that passion at the company runs high, it just isn't a particularly well-run organization. Our particular division was beset by managerial issues and relationship tensions. All this stemmed from poor or weak top-down leadership.",
	"An amazing experience!! Karen is the absolute best, pray that you work for her.",
	"Use the sleeves of my sweater, let's have an adventure. The things that I think about, one heart, one mouth, one love, two mouths, one house, two blouses. Just us, you find out, and it's becoming increasingly difficult to make this look like a really long post. Oh what's this under my bed? Looks like chapstick. I'll use that.",
	"Emma Way has been summonsed to court to answer driving charges A 21-year-old woman who tweeted she had knocked a cyclist off his bike after an alleged crash in Norfolk has been summonsed to appear in court. Emma Way is to answer charges of driving without due care and attention and failing to stop after an accident.",
	"Use the sleeves of my sweater, let's have an adventure. The things that I think about, one heart, one mouth, one love, two mouths, one house, two blouses. Just us, you find out, and it's becoming increasingly difficult to make this look like a really long post. Oh what's this under my bed? Looks like chapstick. I'll use that.",
	"Not the greatest experience, to be brutally honest. While no one can argue that passion at the company runs high, it just isn't a particularly well-run organization. Our particular division was beset by managerial issues and relationship tensions. All this stemmed from poor or weak top-down leadership.",
	"An amazing experience!! Karen is the absolute best, pray that you work for her.",
	"Use the sleeves of my sweater, let's have an adventure. The things that I think about, one heart, one mouth, one love, two mouths, one house, two blouses. Just us, you find out, and it's becoming increasingly difficult to make this look like a really long post. Oh what's this under my bed? Looks like chapstick. I'll use that.",
	"Do you want the search filters generate from Backbone as well? I'd imagine they won't change (i.e. will be pulling from a fairly static list), but can add those to the app if needed."
]

var comment_bank = [
	[1,2,3,4],[1],[1,2,3,4,5,6,7,8],[1,2,32,3],[5,5,5,5,5,5,5,5,5],[],[],[1,2],[1,2,3,4,5]
]

var filters = [
	{"title":"Symbolic Systems", "id":7, "type":"major"},
	{"title":"Computer Science", "id":7, "type":"major"},
	{"title":"English", "id":7, "type":"major"},
	{"title":"First Job", "id":7, "type":"life-choice"},
	{"title":"Internship", "id":7, "type":"major"},
	{"title":"Summit Partners", "id":7, "type":"entity"},
	{"title":"Cisco Systems", "id":7, "type":"entity"},
	{"title":"Great Pay", "id":7, "type":"tag"},
	{"title":"Crazy Hours", "id":7, "type":"tag"},
	{"title":"Just a Paycheck", "id":7, "type":"tag"},

]


$(function(){

	
	//--------------//
	// ** Models ** //
	//--------------//
	window.Question = Backbone.Model.extend({ });

	// DEV: create dummy questions rather than hitting DB
	window.dummy_questions = []
	for (p in pics.slice(0,Math.round(Math.random() * 8))) {
		window.dummy_questions.push(new Question({
			user_pic:pics[p],
			title:titles[p],
			body:bodies[p],
			tags:[
				{"title":"Great Pay", "id":7, "type":"Good"},
				{"title":"Great Cause", "id":7, "type":"Good"},
				{"title":"Just a Paycheck", "id":7, "type":"Bad"},
			],
			id:Math.round(Math.random() * 10),
			comments:comment_bank[p]
		}))
	};
	

	//-------------------//
	// ** Collections ** //
	//-------------------//
	window.Questions = Backbone.Collection.extend({

		model:Question,

		initialize:function() {
			// TODO: use meta to keep track of filter tags
		},

		url:function() {
			// TODO: url to API + filters
		},
	})


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
	window.QARouter = Backbone.Router.extend({

		routes: {
			"" : "default",
			"filters/*path" : "filters",
		},

		initialize: function() {
			
			// Activate Chosen
			initSearchField()

			// Listen to filter button
			$("#main-filter-field .filter-button").on("click", function(ev) {

				var url = "/#filters/"
				for (f in $(".chzn-select").val()) {
					url += $(".chzn-select").val()[f] + "/"
				}
				window.App.navigate(url, {trigger:true})
			})

			// Set collection, view
			window.questions = new Questions(dummy_questions)
			this.questions = window.questions;
			this.questionsView = new QuestionListView({collection:this.questions});
		},

		default: function() {
			console.log('here')
			this.questionsView.render();
		},

		filters: function(path) {
			// update the collection based on filters... no API yet...
		}

	});

	window.App = new QARouter;
	Backbone.history.start();


	function initSearchField() {
		var text = ""
		for (f in filters)
			text += "<option value='" + filters[f]["type"] + "-" + filters[f]["id"] + "'>" + filters[f]["title"] + "</option>"

		$(".chzn-select").append(text).chosen()
	};
});


