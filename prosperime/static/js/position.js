$(document).ready(function() {
    // nav between network and all
    $("a.career-profile-nav").click(function() {
       // see which view is selected
        if ($(this).data('view') == 'network') {
            console.log("showing network info");
            // switch nav classes
            $("a.career-profile-nav[data-view='network']").addClass('selected').removeClass('unselected');
            $("a.career-profile-nav[data-view='all']").addClass('unselected').removeClass('selected');
            // switch charts
            $("div#ed-overview-network-chart").show();
            $("div#ed-overview-all-chart").hide();
            // show all network divs
            $("div[data-view='network']").show();
            $("div[data-view='all']").hide();
            // switch stats
            $("span.carer-profile-stats-block[data-view='network']").addClass('stats-highlighted');
            $("span.carer-profile-stats-block[data-view='all']").removeClass('stats-highlighted');
            $("span.stats-holder[data-view='network']").show();
            $("span.stats-holder[data-view='all']").hide();
        } else {
            console.log("showing all info");
            // switch nav classes
            $("a.career-profile-nav[data-view='all']").addClass('selected').removeClass('unselected');
            $("a.career-profile-nav[data-view='network']").addClass('unselected').removeClass('selected');
            // switch charts
            $("div#ed-overview-all-chart").show();
            $("div#ed-overview-network-chart").hide();
            // show all divs
            $("div[data-view='all']").show();
            $("div[data-view='network']").hide();
            // switch stats
            $("span.carer-profile-stats-block[data-view='all']").addClass('stats-highlighted');
            $("span.carer-profile-stats-block[data-view='network']").removeClass('stats-highlighted');
            $("span.stats-holder[data-view='all']").show();
            $("span.stats-holder[data-view='network']").hide();
        }
    })
});


// kick off app once DOM is ready

$(function(){

    var eatmeat = function(id) {
        // console.log($('#paper-wrapper-' + id))
        // $('#paper-wrapper-' + id).html('<h1>Chillaz</h1>')
        // console.log($('#paper-wrapper-' + id)).html()
    }


    //--------------//
    // ** Models ** //
    //--------------//
    var pos_id = $(".position-info").data("pos-id");
    // Filter: dynamically loaded search param
    window.Filter = Backbone.Model.extend({
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
                'view':'positions'
            };
        },

        model:Filter,
        url: function() {
            // set base path to either company or path filters
            var init_path;
            init_path = "/position_paths_filters/" + pos_id;

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

    // Paths: collection of paths
    window.Paths = Backbone.Collection.extend({
        
        initialize: function() {
            // initialize array of meta data
            this._meta = {};
        },

        model: Path,

        url: function() {
            if (this._meta['query'] === undefined) {
                return '/position_paths/' + pos_id;
            } else {
                return '/position_paths/'+ pos_id + this._meta['query'];
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
    window.filters = new Filters;
    window.paths = new Paths;

    //-------------//
    // ** Views ** //
    //-------------//


    // View: TimelineView
    window.TimelineView = Backbone.View.extend({


        events: {

        },

        initialize: function() {
            _.bindAll(this,'render');

            // Must create the paper container beforehand so that 
            // it exists when render() is called
            this.paper_div = document.createElement("div")

            // No idea why this has to be done, but it does
            this.position_title = position_title 
        },

        render: function() {
            var positions = []
            var all_positions = this.model['positions']
            var length = all_positions.length

            // Sort Positions by Start Date
                // TODO: what happens w/ no start date?
            all_positions = _.sortBy(all_positions, function(el) {
                return el.start_date
            });


            // Only get positions on either side of relevant pos
            for(var i = 0; i < length; i++) {
                if (all_positions[i].title == this.position_title) {
                    if (i < length - 1 && all_positions[i + 1] != this.position_title) {

                        if (i > 0) positions.push(all_positions[i - 1])
                        positions.push(all_positions[i])
                        if (i < length - 1) positions.push(all_positions[i + 1])

                    } else if (i == length - 1 && all_positions[i - 1].title != this.position_title) {
                        
                        if (i > 0) positions.push(all_positions[i - 1])
                        positions.push(all_positions[i])
                        if (i < length - 1) positions.push(all_positions[i + 1])
                    }

                }
            }

 

            /* Timeline Constants */
            var constants = {

                'paper_w':700,
                'paper_h':120,
                'start_offset':25,
                'midline':60,
                'text-attributes':{
                    'font-size':'12',
                    'font-family':'"HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, "Lucida Grande", sans-serif',
                },
                'position_text_height':40,
                'box_style':2,
                'effective_midline':33,
                'top_text_offset':25,
                'bottom_text_offset':15,
            }


            monospaced_timeline(constants, positions, this.paper_div)

            this.$el.append(this.paper_div)
            // need to return the actual html in this case, not the el
            return this.$el.html() 
        },

    });

    // View: PathSingleView
    window.PathSingleView = Backbone.View.extend({

        tagName: "li",
        template:_.template($('#path-single-template').html()),

        events: {

        },

        initialize: function() {
            this.model.on('change',this.render,this);   
        },

        render: function() {

            // Render path container
            var renderedContent = this.template(this.model.toJSON());
            $(this.el).html(renderedContent);

            // Append timeline
            var timelineView = new TimelineView({
                model:this.model.toJSON(),
            });

            var timeline_wrapper = this.$('.search-timeline-container')
            timeline_wrapper.html(timelineView.render())

            return this;
        },

        // renderViz: function() {
        //     var pathURL = "/position/" + this.model.id;
        //     // var renderedPath = pathTemplate(this.model.toJSON());
        //     // $(this.el).find("div.path-viz-long").html(renderedPath);
        //     _gaq.push(['_trackEvent','Search','Show Path',this.model.id])
        //     $(this.el).find("div.path-viz-long").load(pathURL);
        //     $(this.el).find("div.path-viz-short").toggle();
        //     $(this.el).find("div.path-viz-long").toggle();
        // },

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

            var $paths, collection = this.collection;

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
            var orgFilters = $("input[name='Organizations-filters']:checked").map(function(filter) { return this.value });

            // construct URL
            if (locationFilters.length > 0 ) {
                selectedFilters.location = locationFilters;
            }
            if (sectorFilters.length > 0) {
                selectedFilters.sector = sectorFilters;             
            }
            if (orgFilters.length > 0) {
                selectedFilters.org = orgFilters;
            }
            console.log(selectedFilters);
            
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
            App.navigate(filterUrl,{trigger:true});
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


    //---------------//
    // ** Routers ** //
    //---------------//
    window.SearchRouter = Backbone.Router.extend({

        routes: {
            "" : "emptySearch",
            "paths/" : "emptyPathSearch",
            "paths/:query" : "pathSearch",
        },

        initialize: function() {

            // set collections
            
            this.filters = window.filters;
            this.paths = window.paths;

            // set views
            // show paths and path filters by default
            
            this.filtersView = new FilterListView({ collection: this.filters});
            this.pathsView = new PathListView({ collection: this.paths});
            this.filters.fetch();
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
                        //  fullUrl += "+'" + encodeURIComponent(params[key][i]) + "'";
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






// chart functions
Raphael.fn.pieChart = function (cx, cy, r, values, labels, stroke) {
    var paper = this,
        rad = Math.PI / 180,
        chart = this.set();
    function sector(cx, cy, r, startAngle, endAngle, params) {
        var x1 = cx + r * Math.cos(-startAngle * rad),
            x2 = cx + r * Math.cos(-endAngle * rad),
            y1 = cy + r * Math.sin(-startAngle * rad),
            y2 = cy + r * Math.sin(-endAngle * rad);
        return paper.path(["M", cx, cy, "L", x1, y1, "A", r, r, 0, +(endAngle - startAngle > 180), 0, x2, y2, "z"]).attr(params);
    }
    var angle = 0,
        total = 0,
        start = 0,
        process = function (j) {
            var value = values[j],
                angleplus = 360 * value / total,
                popangle = angle + (angleplus / 2),
                color = Raphael.hsb(start, .75, 1),
                ms = 500,
                text_ms = 30,
                delta = 30,
                bcolor = Raphael.hsb(start, 1, 1),
                p = sector(cx, cy, r, angle, angle + angleplus, {fill: "90-" + bcolor + "-" + color, stroke: stroke, "stroke-width": 3});
                //txt = paper.text(100,10,labels[j]).attr({stroke:"none",opacity:0,"font-size":12});
            p.mouseover(function () {
                p.stop().animate({transform: "s1.1 1.1 " + cx + " " + cy}, ms, "elastic");
                $("#position-profile-graph-label").text(labels[j]);
                //txt.stop().animate({opacity: 1}, text_ms, "elastic");
            }).mouseout(function () {
                p.stop().animate({transform: ""}, ms, "elastic");
                //txt.stop().animate({opacity: 0}, text_ms);
            });
            angle += angleplus;
            chart.push(p);
            //chart.push(txt);
            start += .1;
        };
    for (var i = 0, ii = values.length; i < ii; i++) {
        total += values[i];
    }
    for (i = 0; i < ii; i++) {
        process(i);
    }
    return chart;
};

$(function () {
    var network_values = [],
        network_labels = [];
    $("li.ed_overview_network_item").each(function () {
        network_values.push($(this).data('count'));
        network_labels.push($(this).data('name'));
    });
    $("ul.ed_overview_network_graph_list").hide();
    Raphael("ed-overview-network-chart", 275, 250).pieChart(100, 100, 75, network_values, network_labels, "#fff");
    var all_values = [],
        all_labels = [];
    $("li.ed_overview_all_item").each(function () {
        all_values.push($(this).data('count'));
        all_labels.push($(this).data('name'));
    });
    $("ul.ed_overview_all_graph_list").hide();
    Raphael("ed-overview-all-chart", 275, 250).pieChart(100, 100, 75, all_values, all_labels, "#fff");
});