(function () {
    "use strict";

    var website = openerp.website;
    var _t = openerp._t;

    var StatusPie = openerp.Widget.extend({
        init: function (parent, options) {
            this._super.apply(this, arguments);
            this.statuses = options;
        },
        start: function () {
            var self = this;
            this._super.apply(this, arguments);

            var w = 300,
                h = 300,
                r = 150,
                inner_r= 30,
                color = d3.scale.category20c();
            var data = self.statuses;

             var vis = d3.select("#status_chart")
                         .append("svg:svg")
                         .data([data])
                         .attr("width", w)
                         .attr("height", h)
                         .append("svg:g")
                         .attr("transform", "translate(" + r + "," + r + ")")
             var arc = d3.svg.arc()
                             .innerRadius(inner_r)
                             .outerRadius(r);
             var pie = d3.layout.pie()
                                .value(function(d) {
                                    return d.value;
                                });
             var arcs = vis.selectAll("g.slice")
                           .data(pie)
                           .enter()
                           .append("svg:g")
                           .attr("class", "slice");
             arcs.append("svg:path")
                 .attr("fill", function(d, i) { return color(i); } )
                 .attr("d", arc);
             arcs.append("svg:text")
                 .attr("transform", function(d) {
                     d.innerRadius = inner_r;
                     d.outerRadius = r;
                     return "translate(" + arc.centroid(d) + ")";
                 })
                 .attr("text-anchor", "middle")
                 .text(function(d, i) { return data[i].label; });
        },

    });

    website.ready().then(function () {
        var statuses_data = window.statuses;
        delete window.statuses;
        $('script#status_bootstrap').remove();
        var status_pie = new StatusPie(null, statuses_data);
        status_pie.start();
    });

})();
