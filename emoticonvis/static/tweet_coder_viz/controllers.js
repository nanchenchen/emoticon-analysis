(function () {
    'use strict';


    var module = angular.module('TweetCoderViz.controllers', [
        'TweetCoderViz.services',
        'angularSpinner',
        'angucomplete-alt',
        'smart-table'
    ]);

    module.config(['$interpolateProvider', function ($interpolateProvider) {
        $interpolateProvider.startSymbol('{$');
        $interpolateProvider.endSymbol('$}');
    }]);


    module.config(['usSpinnerConfigProvider', function (usSpinnerConfigProvider) {
        usSpinnerConfigProvider.setDefaults({
            color: '#111'
        });
    }]);

    var DictionaryController = function ($scope, Dictionary) {
        $scope.Dictionary = Dictionary;

    };
    DictionaryController.$inject = [
        '$scope',
        'TweetCoderViz.services.Dictionary'
    ];
    module.controller('TweetCoderViz.controllers.DictionaryController', DictionaryController);

    var ViewController = function ($scope, $timeout, Dictionary, SVMResult, FeatureVector, usSpinnerService) {

        $scope.showReview = { visible: true };

        var sortOption_None = 0;
        var sortOption_Descending = 1;
        var sortOption_Ascending = 2;

        var toggleSort = function(previousSortOption){
            return (previousSortOption+1) % 3;
        };

        $scope.fullColors =
            [["#f6faea","#e5f1c0","#d4e897","#bada58","#98bc29","#769220","#556817","#333f0e","#222a09"],
            ["#f4eef6","#dfcde4","#bf9cc9","#aa7bb7","#865195","#683f74","#4a2d53","#35203b","#1e1221"],
            ["#fce8f1","#f7bbd4","#f28db7","#ec5f9a","#e41b6e","#b71558","#911146","#720d37","#440821"],
            ["#e9f0fb","#bed1f4","#92b3ed","#5185e1","#2361cf","#1a4899","#12336d","#0b1f41","#07142c"],
            ["#fff5eb","#fee6ce","#fdd0a2","#fdae6b","#fd8d3c","#f16913","#d94801","#a63603","#7f2704"]];

        $scope.spinnerOptions = {
            radius: 20,
            width: 6,
            length: 10,
            color: "#000000"
        };

        // Labeling pane
        $scope.currentMessage = undefined;
        $scope.currentLabel = undefined;
        $scope.isCurrentMessageAmbiguous = false;
        $scope.codes = undefined;

        // review pane
        $scope.submittedLabels = undefined;
        $scope.selectedLabelFilter = undefined;
        $scope.filteredLabels = undefined;

        // review-confusion
        $scope.filteredReviewLabels = [];
        $scope.selectedCells = undefined;

        // review-scatter
        $scope.featureCallbacks = {
            onFeatureHover: undefined
        };

        // feature pane
        $scope.features = undefined;
        $scope.featureSortKey = { user: undefined, system: undefined };
        $scope.featureSortOption = { user: sortOption_None, system: sortOption_None };

        // Feature selection logic and states
        $scope.hoveredCharStart = -1;
        $scope.hoveredCharEnd = -1;
        $scope.clickStartTokenItem = undefined;
        $scope.selectedTokens = undefined;
        $scope.selectedTokenIndices = new Map();

        var tweetItem = function(messageData) {
            var text = messageData.message.text;
            var characters = text.split("");
            var tokens = messageData.tokens;

            var tokenItems = [];
            var charToToken = [];

            var lowerText = text.toLowerCase();
            var currentIndex = 0;
            for (var i = 0; i < tokens.length; i++) {
                var token = tokens[i];
                if (token != null && token.length > 0) {
                    var foundIndex = lowerText.substr(currentIndex).indexOf(token) + currentIndex;

                    var tokenItem = {
                        text: token,
                        index: i
                    };

                    currentIndex = foundIndex;
                    tokenItem.startIndex = currentIndex;
                    currentIndex += token.length - 1;
                    tokenItem.endIndex = currentIndex;

                    tokenItems.push(tokenItem);

                    for (var j = tokenItem.startIndex; j <= tokenItem.endIndex; j++) {
                        charToToken[j] = i;
                    }
                }
            }

            return {
                id: messageData.message.id,
                text: text,
                tokens: tokenItems,
                characters: characters,
                charToToken: charToToken,
                features: messageData.feature_vector
            };
        };

        var load = function(){
            var request = SVMResult.load(Dictionary.id);
            if (request) {
                usSpinnerService.spin('label-spinner');
                request.then(function() {
                    usSpinnerService.stop('label-spinner');
                    var modelData = SVMResult.data.results;
                    var messages = SVMResult.data.messages;

                    $scope.codes = modelData.codes;

                    $scope.selectedCells = [];
                    $scope.codes.forEach(function(codei, i) {
                        $scope.selectedCells[i] = $scope.codes.map(function(codej, j){
                            return false;
                        });
                    });

                    // Map message id to model output
                    var modelOutputMap = new Map();
                    for (var i = 0; i < modelData.train_id.length; i++){
                        modelOutputMap.set(modelData.train_id[i], {
                            prediction: modelData.predictions[i],
                            probabilities: modelData.probabilities[i],
                            label: modelData.labels[i]
                        });
                    }

                    var tweetItems = [];

                    // Merge training result with messages
                    for (var i = 0; i < messages.length; i++) {
                        var message = messages[i];
                        var modelOutput = modelOutputMap.get(message.message.id);

                        var item = tweetItem(message);
                        item.prediction = modelOutput.prediction;
                        item.probabilities = modelOutput.probabilities;
                        item.label = modelOutput.label;

                        tweetItems.push(item);
                    }

                    $scope.submittedLabels = tweetItems;
                    $scope.filteredReviewLabels = $scope.submittedLabels;

                    $scope.filterLabels("all");

                    $scope.features = {
                        user: [],
                        system: modelData.features
                    };
                });
            }
        };

        var getMessage = function(){
            var request = FeatureVector.load(128);
            if (request) {
            usSpinnerService.spin('label-spinner');
                request.then(function() {
                    usSpinnerService.stop('label-spinner');
                    $scope.currentMessage = tweetItem(FeatureVector.data);
                    $scope.selectLabel(null);
                    $scope.isCurrentMessageAmbiguous = false;
                });
            }
        };

        $scope.selectLabel = function(label){
            $scope.currentLabel = label;
        };

        $scope.submitLabel = function(){
            $scope.getMessage();
        };

        $scope.sortFeatures = function(featureType, key){
            // Check if the sort key has changed
            if ($scope.featureSortKey[featureType] == key){
                $scope.featureSortOption[featureType] = toggleSort($scope.featureSortOption[featureType]);
            }
            else {
                $scope.featureSortKey[featureType] = key;
                $scope.featureSortOption[featureType] = sortOption_Descending;
            }

            if ($scope.featureSortOption[featureType] == sortOption_None) {
                $scope.featureSortKey[featureType] = undefined;
                $scope.features[featureType].sort(function (a, b) {
                    return a.index - b.index;
                });
            }
            else {
                $scope.features[featureType].sort(function (a, b) {
                    var sign = $scope.featureSortOption[featureType] == sortOption_Ascending ? 1 : -1;
                    var key = $scope.featureSortKey[featureType];
                    switch (key) {
                        case "word":
                            return sign * ((a.feature.toLowerCase() <= b.feature.toLowerCase()) ? -1 : 1);
                        case "count":
                            return sign * (a.count - b.count);
                        default:
                            return sign * (a.codes[key].weight - b.codes[key].weight);
                    }
                });
            }
        };

        $scope.filterLabels = function(filter) {
            if ($scope.selectedLabelFilter != filter) {
                $scope.selectedLabelFilter = filter;
                $scope.filteredLabels = $scope.submittedLabels.filter(function (item) {
                    switch (filter) {
                        case "all":
                            return true;
                        case "gold":
                            return item.label.gold != null;
                        case "ambiguous":
                            return item.label.ambiguous;
                        case "disagreement":
                            return item.label != item.prediction;
                        default:
                            return item.label != null && item.label == filter;
                    }
                });
            }
        };

        var updateSelection = function(startIndex, endIndex, isSelected, shouldClear) {
            if (shouldClear) {
                $scope.selectedTokenIndices.clear();
            }

            for (var i = startIndex; i <= endIndex; i++) {
                var existing = $scope.selectedTokenIndices.get(i);
                if (existing == i && !isSelected) {
                    $scope.selectedTokenIndices.delete(i);
                }
                else if (existing != i && isSelected) {
                    $scope.selectedTokenIndices.set(i, i);
                }
            }
        };

        var isTokenSelectedAtCharIndex = function (charIndex){
            if ($scope.currentMessage) {
                var tokenIndex = $scope.currentMessage.charToToken[charIndex];
                if (tokenIndex != undefined && $scope.selectedTokenIndices.get(tokenIndex) == tokenIndex) {
                    return true;
                }
            }

            return false;
        };

        $scope.onCharMouseEnter = function(charIndex){
            //console.log("onCharMouseEnter:" + charIndex);

            if ($scope.currentMessage){
                var tokenIndex = $scope.currentMessage.charToToken[charIndex];

                if (tokenIndex != undefined && $scope.currentMessage.tokens[tokenIndex] != undefined) {
                    var tokenItem = $scope.currentMessage.tokens[tokenIndex];
                    $scope.hoveredCharStart = tokenItem.startIndex;
                    $scope.hoveredCharEnd = tokenItem.endIndex;

                    // If we're in the middle of selection, update selected char indices
                    if ($scope.clickStartTokenItem != undefined) {

                        var ctrlClick = event.ctrlKey || (event.metaKey && !event.ctrlKey);

                        if (tokenIndex < $scope.clickStartTokenItem.index) {
                            updateSelection(tokenIndex, $scope.clickStartTokenItem.index, true, !ctrlClick);
                        }
                        else if (tokenIndex > $scope.clickStartTokenItem.index) {
                            updateSelection($scope.clickStartTokenItem.index, tokenIndex, true, !ctrlClick);
                        }
                    }
                }
                else {
                    $scope.hoveredCharStart = -1;
                    $scope.hoveredCharEnd = -1;
                }
            }
        };

        $scope.onCharMouseLeave = function(charIndex){
            //console.log("onCharMouseLeave:" + charIndex);

            $scope.hoveredCharStart = -1;
            $scope.hoveredCharEnd = -1;
        };

        $scope.onCharMouseDown = function(charIndex, event){
            //console.log("onCharMouseDown:" + charIndex);

            if ($scope.currentMessage) {

                var tokenIndex = $scope.currentMessage.charToToken[charIndex];

                if (tokenIndex != undefined && $scope.currentMessage.tokens[tokenIndex] != undefined) {

                    var tokenItem = $scope.currentMessage.tokens[tokenIndex];

                    var ctrlClick = event.ctrlKey || (event.metaKey && !event.ctrlKey);

                    // if there was a selection at this tokenIndex and mouse was clicked with command/ctrl button,
                    // clear the selection on this token index
                    if ($scope.selectedTokenIndices.get(tokenIndex) == tokenIndex && ctrlClick) {
                        $scope.clickStartTokenItem = undefined;
                        updateSelection(tokenIndex, tokenIndex, false, false);
                    }
                    else {
                        $scope.clickStartTokenItem = tokenItem;
                        updateSelection(tokenIndex, tokenIndex, true, !ctrlClick);
                    }
                }
                else {
                    $scope.clickStartTokenItem = undefined;
                    $scope.selectedTokenIndices.clear();
                }
            }
        };

        $scope.onCharMouseUp = function(charIndex) {
            $scope.clickStartTokenItem = undefined;
            $scope.selectedTokens = undefined;

            if ($scope.selectedTokenIndices.size > 0) {
                if ($scope.currentMessage) {

                    // Get sorted list of selected token indices
                    var indices = [];
                    $scope.selectedTokenIndices.forEach(function (val) {
                        indices.push(val);
                    });
                    indices.sort(function (a, b) {
                        return a - b;
                    });

                    var tokens = [];
                    var currentTokenIndex = -1;
                    for (var i = 0; i < indices.length; i++) {
                        var tokenIndex = indices[i];

                        if (tokenIndex != currentTokenIndex) {
                            tokens.push($scope.currentMessage.tokens[tokenIndex].text);
                            currentTokenIndex = tokenIndex;
                        }
                    }

                    $scope.selectedTokens = tokens;
                }
            }
        };

        $scope.charStyle = function(charIndex) {
            var style = {};
            if (charIndex >= $scope.hoveredCharStart && charIndex <= $scope.hoveredCharEnd) {
                style["background"] = "#ffcc99";
            }


            if (isTokenSelectedAtCharIndex(charIndex) || (isTokenSelectedAtCharIndex(charIndex - 1) && isTokenSelectedAtCharIndex(charIndex + 1))) {
                style["background"] = "#ff6600";
            }
            return style;
        };

        $scope.codeStyle = function(codeIndex, code, selected){

            var colorIndex = 0;
            if (codeIndex < $scope.fullColors.length) { colorIndex = codeIndex;}
            var colors = $scope.fullColors[colorIndex];

            var css = {
                'background-color' : '#eee',
                'color': '#eee'
            };

            if (code != null) {
                var code_order = (Math.floor(code.order / 2));
                if (code_order < colors.length) {
                    css['background-color'] = colors[colors.length - code_order - 1];
                    css['color'] = colors[colors.length - code_order - 1];
                }
            }
            else {
                css['background-color'] = colors[colors.length - 5];
                css['color'] = colors[colors.length - 5];
            }

            return css;
        };

        $scope.buttonStyle = function(code){

            var colorIndex = 0;
            if (code.index < $scope.fullColors.length) { colorIndex = code.index;}
            var colors = $scope.fullColors[colorIndex];
            var color = colors[colors.length - 5];

            var css = {
                border: 'solid 1px ' + color
            };

            if (code.text == $scope.currentLabel){
                css['background-color'] = color;
            }
            else {
                css['color'] = color;
            }

            return css;
        };

        $scope.labelStyle = function(label) {

            if (label != undefined) {
                var colorIndex = 0;
                if (label < $scope.fullColors.length) {
                    colorIndex = label;
                }
                var colors = $scope.fullColors[colorIndex];
                var color = colors[colors.length - 5];

                var css = {
                    'background-color': color,
                    'color': label.ambiguous ? 'white' : color
                };

                return css;
            }
            return "";
        };

        $scope.boxColor = function(codeIndex) {

            var colorIndex = 0;
            if (codeIndex < $scope.fullColors.length) {
                colorIndex = codeIndex;
            }
            var colors = $scope.fullColors[colorIndex];
            var color = colors[colors.length - 5];

            return color;
        };

        $scope.selectCells = function(labelPredictionPairs, selected) {
            for (var i = 0; i < labelPredictionPairs.length; i++) {
                var pair = labelPredictionPairs[i];
                $scope.selectedCells[pair.prediction][pair.label] = selected;
            }

            var selected = false;
            for (var i = 0; i < $scope.selectedCells.length; i++) {
                for (var j = 0; j < $scope.selectedCells.length; j++) {
                    if ($scope.selectedCells[i][j]){
                        selected = true;
                        break;
                    }
                }

                if (selected){
                    break;
                }
            }

            if (selected) {
                $scope.filteredReviewLabels = $scope.submittedLabels.filter(function (item) {
                    return $scope.selectedCells[item.prediction][item.label];
                });
            }
            else {
                $scope.filteredReviewLabels = $scope.submittedLabels;
            }

            $scope.$apply();
        };

        $scope.onFeatureMouseOver = function(feature){
          if ($scope.featureCallbacks.onFeatureHover){
              $scope.featureCallbacks.onFeatureHover(feature.feature_index);
          }
        };

        $scope.onFeatureMouseLeave = function(feature){
          if ($scope.featureCallbacks.onFeatureHover){
              $scope.featureCallbacks.onFeatureHover(-1);
          }
        };

        // load the svm results
        load();

        // fetch a message to label
        getMessage();
    };

    ViewController.$inject = [
        '$scope',
        '$timeout',
        'TweetCoderViz.services.Dictionary',
        'TweetCoderViz.services.SVMResult',
        'TweetCoderViz.services.FeatureVector',
        'usSpinnerService'
    ];
    module.controller('TweetCoderViz.controllers.ViewController', ViewController);

    module.directive('tweetItems', function () {
         var TweetItems = function (scope, $element, attrs) {

            var DEFAULT_VALUE_KEY = 'value';

            var width = 300;
            var height = 300;
            var heightPerCode = height / scope.codes.length;
             var margin = 5;

            var self = this;
            var codes = scope.codes;
            var boxColor = scope.boxColor;
            var svg = d3.select($element[0]).append('svg')
                .attr('width', width)
                .attr('height', height);

            var codeBox = svg.selectAll('.code')
                .data(codes)
                .enter()
                .append('g')
                .attr('class', 'code')
                .attr('transform', function(c,i) { return 'translate(0,'+ (i * heightPerCode + margin) + ')';})
                .attr('width', width)
                .attr('height', heightPerCode - 2 * margin);

            self.render = function (data) {
                if (!data) {
                    return;
                }

                var boxSize = 10;
                var boxSpacing = 2;
                var colCount = Math.floor((heightPerCode - 2 * margin) / (boxSize + boxSpacing));

                codeBox.each(function(code){
                    var box = d3.select(this);

                    var labels = data.filter(function(d) { return d.label == code.index; });
                    var i = 0;
                    var tweets = box.selectAll('.tweet-box')
                        .data(labels, function(l) {
                            l.index = i++;
                            return l.id;
                        });

                    tweets.enter().append("rect")
                        .attr("class", "tweet-box")
                        .attr("x", function(l) {
                            var row = Math.floor(l.index / colCount);
                            return row * (boxSize + boxSpacing); })
                        .attr("y", function(l) {
                            var col = l.index % colCount;
                            return col * (boxSize + boxSpacing);
                        })
                        .attr("width", boxSize)
                        .attr("height", boxSize)
                        .attr("fill", boxColor(code.index))
                        .attr("data-item", function(l) { return JSON.stringify(l); });

                    tweets.exit().remove();
                });
            };
        };

        return {
            restrict: 'EA',
            scope: {
                data: '=',
                codes: '=',
                boxColor: "="
            },
            link: function (scope, element, attrs) {

                if (!scope._TweetItems) {
                    var vis = scope._TweetItems = new TweetItems(scope, element, attrs);

                    // Watch for changes to the data
                    scope.$watch('data', function (newVals, oldVals) {
                        return vis.render(scope.data);
                    }, false);

                } else {
                    throw("What is this madness");
                }
            }
        };
    });

    module.directive('scatterBox', function () {
         var ScatterBox = function (scope, $element, attrs) {

            var width = 460;
            var height = 270;
             var margin = { top: 0, left: 0, right: 0, bottom: 15};
            var widthPerCode = (width - margin.left - margin.right) / scope.codes.length;
             var codeMargin = 5;

            var self = this;
            var codes = scope.codes;
            var boxColor = scope.boxColor;
             var callbacks = scope.featureCallbacks;
            var svg = d3.select($element[0]).append('svg')
                .attr('width', width - margin.left - margin.right)
                .attr('height', height - margin.top - margin.bottom);

            var codeBox = svg.selectAll('.code')
                .data(codes)
                .enter()
                .append('g')
                .attr('class', 'code')
                .attr('transform', function(c,i) { return 'translate(' + (i * widthPerCode + codeMargin) + ',' + '0)';})
                .attr('width', widthPerCode - 2 * codeMargin)
                .attr('height', height - margin.top - margin.left);

            self.render = function (data) {
                if (!data) {
                    return;
                }

                callbacks.onFeatureHover = function(featureIndex){
                    svg.selectAll(".scatter-box")
                        .transition()
                        .duration(200)
                        .style("opacity", function(item){
                            if (featureIndex == -1){
                                return 1;
                            }
                            else if (item.features[featureIndex] > 0){
                                return 1;
                            }
                            else {
                                return 0.3;
                            }
                        });
                };

                var boxSize = 8;
                var boxSpacing = 4;
                var colCount = Math.floor((widthPerCode - 2 * codeMargin) / (boxSize + boxSpacing));

                codeBox.each(function(code){
                    var box = d3.select(this);

                    box.append('text')
                        .text(code.text)
                        .attr("fill", boxColor(code.index))
                        .attr("transform", "translate(0," + (height - margin.bottom - margin.top - 5) + ")");

                    var labels = data.filter(function(d) { return d.label == code.index; });
                    var i = 0;
                    var tweets = box.selectAll('.scatter-box')
                        .data(labels, function(l) {
                            l.index = i++;
                            return l.id;
                        });

                    tweets.enter().append("rect")
                        .attr("class", "scatter-box")
                        .attr("x", function(l) {
                            var col = l.index % colCount;
                            return col * (boxSize + boxSpacing);
                        })
                        .attr("y", function(l) {
                            var row = Math.floor(l.index / colCount) + 3;
                            return height - margin.top - margin.bottom - row * (boxSize + boxSpacing);
                        })
                        .attr("width", boxSize)
                        .attr("height", boxSize)
                        .attr("stroke-width", 2)
                        .attr("stroke", function(l) { return boxColor(l.prediction); })
                        .attr("fill", boxColor(code.index));

                    tweets.exit().remove();
                });
            };
        };

        return {
            restrict: 'EA',
            scope: {
                data: '=',
                codes: '=',
                boxColor: "=",
                featureCallbacks: "="
            },
            link: function (scope, element, attrs) {

                if (!scope._ScatterBox) {
                    var vis = scope._ScatterBox = new ScatterBox(scope, element, attrs);

                    // Watch for changes to the data
                    scope.$watch('data', function (newVals, oldVals) {
                        return vis.render(scope.data);
                    }, false);

                } else {
                    throw("What is this madness");
                }
            }
        };
    });

    module.directive('confusionBox', function () {
         var ConfusionBox = function (scope, $element, attrs) {

             var self = this;
             var codes = scope.codes;
             var selectCells = scope.selectCells;

             var width = 460;
             var height = 270;
             var margin = { top: 0, left: 0, right: 0, bottom: 15};
             var textSpacing = { top: 30, left: 60};
             var cellSpacing = 2;
             var rowHeight = (height - margin.top - margin.bottom - textSpacing.top) / codes.length;
             var colWidth = (width - margin.left - margin.right - textSpacing.left) / codes.length;

             var colors = ['#f7f7f7','#cccccc','#969696','#636363','#252525'];
             var svg = d3.select($element[0]).append('svg')
                .attr('width', width - margin.left - margin.right)
                .attr('height', height - margin.top - margin.bottom);

             self.render = function (data) {
                if (!data) {
                    return;
                }

                // split the data
                 var codeMap = d3.range(codes.length);
                 codes.forEach(function(code, i) {
                     codeMap[code.index] = i;
                 });

                var matrix = [];
                 codes.forEach(function(codei, i) {
                     matrix[i] = codes.map(function(codej, j){
                        return {
                            label: codej,
                            prediction: codei,
                            items: [],
                            itemCount: 0
                        }
                     });
                 });

                 var maxCount = 0;
                 data.forEach(function(item){
                    var j = codeMap[item.label];
                     var i = codeMap[item.prediction];
                     matrix[i][j].items.push(item);
                     matrix[i][j].itemCount++;

                     maxCount = Math.max(maxCount, matrix[i][j].itemCount);
                 });


                 var colorScale = d3.scale.quantile()
                  .domain([0, colors.length - 1, maxCount])
                  .range(colors);

                var row = svg.selectAll(".row")
                    .data(matrix)
                    .enter().append("g")
                    .attr("class", "row")
                    .attr("transform", function(d, i) { return "translate(" + textSpacing.left + "," + (i * rowHeight + textSpacing.top) + ")"; })
                    .each(renderRow);

                row.append("text")
                    .attr("x", -10)
                    .attr("text-anchor", "end")
                    .attr("transform", "rotate(-45)")
                    .text(function(d, i) { return codes[i].text; })
                    .on('click', selectRow);

                var column = svg.selectAll(".column")
                    .data(matrix)
                    .enter().append("g")
                    .attr("class", "column")
                    .attr("transform", function(d, i) { return "translate(" + i * colWidth + ", " + textSpacing.top + ")"; });

                column.append("text")
                    .attr("x", textSpacing.left)
                    .attr("y", - textSpacing.top / 2)
                    .attr("text-anchor", "start")
                    .text(function(d, i) { return codes[i].text; })
                    .on('click', function(c) { return selectRow(c, true);});

                function renderRow(row) {
                    var cell = d3.select(this).selectAll(".cell")
                        .data(row)
                        .enter().append("rect")
                        .attr("class", "cell")
                        .attr("id", function(d) { return "cell" + d.label.index + "_" + d.prediction.index; })
                        .attr("x", function(d, i) { return i * colWidth; })
                        .attr("width", colWidth - cellSpacing)
                        .attr("height", rowHeight - cellSpacing)
                        .style("fill", function(d) {
                            if (d.itemCount > 0) {
                                return colorScale(d.itemCount);
                            }
                            else {
                                return 'transparent';
                            }
                        })
                        .on('click', selectCell)
                        .attr("data-val", function(d) { return d.itemCount; });
                }

                function selectRow(row, isCol) {
                    row.selected = !row.selected;
                    d3.select(this).classed("selected", row.selected);

                    var selection = row.map(function(r) {
                        var i = isCol ? r.prediction.index : r.label.index;
                        var j = isCol ? r.label.index: r.prediction.index;
                        svg.select("#cell" + i + "_" + j).classed("selected", row.selected);

                        return {
                        label: r.label.index,
                        prediction: r.prediction.index
                    }});

                    selectCells(selection, row.selected);
                }

                function selectCell(item) {
                    item.selected = !d3.select(this).classed("selected");
                    d3.select(this).classed("selected", item.selected);
                    selectCells([{ label: item.label.index, prediction: item.prediction.index }], item.selected);
                }
            };
        };

        return {
            restrict: 'EA',
            scope: {
                data: '=',
                codes: '=',
                selectCells: "="
            },
            link: function (scope, element, attrs) {

                if (!scope._ConfusionBox) {
                    var vis = scope._ConfusionBox = new ConfusionBox(scope, element, attrs);

                    // Watch for changes to the data
                    scope.$watch('data', function (newVals, oldVals) {
                        return vis.render(scope.data);
                    }, false);

                } else {
                    throw("What is this madness");
                }
            }
        };
    });
})();
