var margin = {top: 100, right: 50, bottom: 50, left: 50};
var graph_width = screen.width - margin.left - margin.right;
var graph_height = screen.height - margin.top - margin.bottom - 150;

var x = d3.scale.linear().range([0, graph_width]);
var y = d3.scale.linear().range([0, graph_height]);

var chart = d3.select(".chart")
    .attr("width", graph_width + margin.left + margin.right)
    .attr("height", graph_height + margin.top + margin.bottom);

var graph = chart.append("g");

var x_axis = graph.selectAll("g")
    .data(headers)
    .enter().append("g")
        .attr("id", function(d, i) { return ids[i];});

axises.append("line")
    .attr("transform", function(d, i) { return "translate(" + (margin.left + x(i)) + ", " + margin.top + ")"; })
    .attr("x1", 0)
    .attr("y1", 0)
    .attr("x2", 0)
    .attr("y2", graphHeight)
    .attr("stroke-width", 3)
    .attr("stroke", "black");

axises.append("text")
    .attr("transform", function(d, i) { return "translate(" + (margin.left + x(i)) + ", " + margin.top + ")"; })
    .attr("dy", graphHeight + 15)
    .style("fill", "gray")
    .style("text-anchor", "middle")
    .text(function(d) { return d;});

var axValues = axises.append("g");

d3.csv("../data/hua.csv", type, function(error, data) {
    var maxVals = [d3.max(data, function(d) { return d.maxCPU; }), d3.max(data, function(d) { return d.maxAcc; }), d3.max(data, function(d) { return d.deltaCPU; }), d3.max(data, function(d) { return d.deltaAcc; })];

    yMaxCpu.domain([0, d3.max(data, function(d) { return d.maxCPU; })]);
    yMaxAcc.domain([0, d3.max(data, function(d) { return d.maxAcc; })]);
    yDeltaCpu.domain([0, d3.max(data, function(d) { return d.deltaCPU; })]);
    yDeltaAcc.domain([0, d3.max(data, function(d) { return d.deltaAcc; })]);

    axValues.append("text")
        .attr("class", "maxVal")
        .attr("transform", function(d, i) { return "translate(" + (margin.left + x(i)) + ", " + margin.top + ")"; })
        .attr("dy", -15)
        .style("fill", "gray")
        .style("text-anchor", "middle")
        .text(function(d, i) { return maxVals[i];});

    lines1.selectAll("g")
    .data(data)
    .enter().append("g").append("line")
        .attr("class", function(d) { return d.dataset + " " + d.popularityTime + " " + d.dataTier + " " + d.sizeGb + " " + d.age + " selected";})
        .attr("x1", function() { return margin.left + x(0);})
        .attr("y1", function(d) { return (margin.top + graphHeight) -  yMaxCpu(d.maxCPU);})
        .attr("x2", function() { return margin.left + x(1);})
        .attr("y2", function(d) { return (margin.top + graphHeight) - yMaxAcc(d.maxAcc);})
        .attr("stroke-width", 1)
        .attr("stroke", "steelblue");

    lines2.selectAll("g")
    .data(data)
    .enter().append("g").append("line")
        .attr("class", function(d) { return d.dataset + " " + d.popularityTime + " " + d.dataTier + " " + d.sizeGb + " " + d.age + " selected";})
        .attr("x1", function() { return margin.left + x(1);})
        .attr("y1", function(d) { return (margin.top + graphHeight) -  yMaxAcc(d.maxAcc);})
        .attr("x2", function() { return margin.left + x(2);})
        .attr("y2", function(d) { return (margin.top + graphHeight) - yDeltaCpu(d.deltaCPU);})
        .attr("stroke-width", 1)
        .attr("stroke", "steelblue");

    lines3.selectAll("g")
    .data(data)
    .enter().append("g").append("line")
        .attr("class", function(d) { return d.dataset + " " + d.popularityTime + " " + d.dataTier + " " + d.sizeGb + " " + d.age + " selected";})
        .attr("x1", function() { return margin.left + x(2);})
        .attr("y1", function(d) { return (margin.top + graphHeight) -  yDeltaCpu(d.deltaCPU);})
        .attr("x2", function() { return margin.left + x(3);})
        .attr("y2", function(d) { return (margin.top + graphHeight) - yDeltaAcc(d.deltaAcc);})
        .attr("stroke-width", 1)
        .attr("stroke", "steelblue");

    var dataTiers = d3.nest()
        .key(function(d) { return d.dataTier;}).sortKeys(d3.ascending)
        .entries(data);

    var ySelections = d3.scale.linear().domain([0, dataTiers.length]).range([0, dataTiers.length*15]);

    selections.selectAll("g")
    .data(dataTiers)
    .enter().append("text")
        .attr("transform", function(d, i) { return "translate(" + (margin.left + graphWidth - x(1) + 20) + ", " + (margin.top + (graphHeight/3) + 15 + ySelections(i)) + ")"; })
        .style("fill", "steelblue")
        .style("stroke-width", 0)
        .style("text-anchor", "start")
        .text(function(d) { return d.key;})
        .on("mouseover", function(){
            d3.select(this).attr("cursor", "pointer");
        })
        .on("click", function(d){
            d3.selectAll(".selected")
                .style("stroke", "steelblue")
                .style("fill", "steelblue")
                .classed("selected", false);
            d3.select(this).classed("selected", true)
                .style("fill", "orange");
            d3.selectAll("." + d.key)
                .classed("selected", true)
                .style("stroke", "orange")
                .each(function () {
                    this.parentNode.parentNode.appendChild(this.parentNode);
                });});
});

function type(d) {
    d.dataset_name = d.dataset_name;
    d.date = +d.date;
    d.accesses = +d.accesses;
    d.size_gb = +d.size_gb;
    d.data_tier = d.data_tier;
    return d;
}