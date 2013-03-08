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
            $("span[data-view='network']").addClass('stats-highlighted');
            $("span[data-view='all']").removeClass('stats-highlighted');
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
            $("span[data-view='all']").addClass('stats-highlighted');
            $("span[data-view='network']").removeClass('stats-highlighted');
        }
    })
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
                $("#career-profile-graph-label").text(labels[j]);
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