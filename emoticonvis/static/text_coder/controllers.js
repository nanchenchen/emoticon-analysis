(function () {
    'use strict';


    var module = angular.module('TextCoder.controllers', [
        'TextCoder.services',
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
        'TextCoder.services.Dictionary'
    ];
    module.controller('TextCoder.controllers.DictionaryController', DictionaryController);

    var ViewController = function ($scope, Dictionary, SVMResult, FeatureVector, UserFeatures, usSpinnerService) {

        $scope.spinnerOptions = {
            radius: 20,
            width: 6,
            length: 10,
            color: "#000000"
        };
        var dist_max_height = 20; // in pixel

        $scope.svm_results = undefined;
        $scope.vector = undefined;
        $scope.features = [];

        $scope.load = function(){
            var request = SVMResult.load(Dictionary.id);
            if (request) {
                usSpinnerService.spin('table-spinner');
                request.then(function() {
                    usSpinnerService.stop('table-spinner');
                    SVMResult.dist_scale.range([0, dist_max_height]);
                    $scope.svm_results = SVMResult.data;
                });
            }

        };

        // load the svm results
        $scope.load();

        $scope.style = function(code, codeIndex){
            var fullColors = 
                [["#f6faea","#e5f1c0","#d4e897","#bada58","#98bc29","#769220","#556817","#333f0e","#222a09"],
                ["#f4eef6","#dfcde4","#bf9cc9","#aa7bb7","#865195","#683f74","#4a2d53","#35203b","#1e1221"],
                ["#fce8f1","#f7bbd4","#f28db7","#ec5f9a","#e41b6e","#b71558","#911146","#720d37","#440821"],
                ["#e9f0fb","#bed1f4","#92b3ed","#5185e1","#2361cf","#1a4899","#12336d","#0b1f41","#07142c"],
                ["#fff5eb","#fee6ce","#fdd0a2","#fdae6b","#fd8d3c","#f16913","#d94801","#a63603","#7f2704"]];
            
            var colorIndex = 0;
            if (codeIndex < fullColors.length) { colorIndex = codeIndex;}
            var colors = fullColors[colorIndex];

            var css = {
                'background-color' : 'none',
                'color': 'black'
            };
            var code_order = (Math.floor(code.order / 2));
            if (code_order  < colors.length ){
                css['background-color'] = colors[colors.length - code_order  - 1];
                if ( code_order  < 3)
                    css['color'] = '#ccc';
            }
            return css;
        };
        $scope.dist = function(code){
            var css = {
                'background-color': 'steelblue',
                'width' : 15,
                'height': SVMResult.dist_scale(code.train_count)
            };
            return css;
        };
        $scope.on_off = function(count){
            var css = {
                'background-color' : 'none',
                'color': 'black'
            };
            if (count > 0){
                css['background-color'] = "#fee0d2";
                //css['color'] = '#ccc';
            }
            return css;
        };
        $scope.active = function(tid){
            return ($scope.vector && $scope.vector.message.id == tid) ? "active" : "";
        };

        $scope.load_vector = function(tid){
            var request = FeatureVector.load(tid);
            if (request) {
                usSpinnerService.spin('vector-spinner');
                request.then(function() {
                    usSpinnerService.stop('vector-spinner');

                    var text = FeatureVector.data.message.text;
                    var characters = text.split("");
                    var tokens = FeatureVector.data.tokens;

                    var tokenItems = [];
                    var charToToken = [];

                    var lowerText = text.toLowerCase();
                    var currentIndex = 0;
                    for (var i = 0; i < tokens.length; i++)
                    {
                        var token = tokens[i];
                        if (token != null && token.length > 0)
                        {
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

                            for (var j = tokenItem.startIndex; j <= tokenItem.endIndex; j++)
                            {
                                charToToken[j] = i;
                            }
                        }
                    }

                    $scope.vector = FeatureVector.data;
                    $scope.vector.message.tokens = tokenItems;
                    $scope.vector.message.characters = characters;
                    $scope.vector.message.charToToken = charToToken;
                });
            }
        };

        $scope.getter = {
            'vector': function(feature){
                return $scope.vector.feature_vector[feature.feature_index];
            }
        };

        // Feature selection logic and states
        $scope.hoveredCharStart = -1;
        $scope.hoveredCharEnd = -1;
        $scope.clickStartTokenItem = undefined;
        $scope.selectedTokens = undefined;
        $scope.selectedTokenIndices = new Map();

        $scope.featureList = {};

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
            if ($scope.vector && $scope.vector.message) {
                var tokenIndex = $scope.vector.message.charToToken[charIndex];
                if (tokenIndex != undefined && $scope.selectedTokenIndices.get(tokenIndex) == tokenIndex) {
                    return true;
                }
            }

            return false;
        };

        $scope.onCharMouseEnter = function(charIndex){
            //console.log("onCharMouseEnter:" + charIndex);

            if ($scope.vector && $scope.vector.message){
                var tokenIndex = $scope.vector.message.charToToken[charIndex];

                if (tokenIndex != undefined && $scope.vector.message.tokens[tokenIndex] != undefined) {
                    var tokenItem = $scope.vector.message.tokens[tokenIndex];
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

            if ($scope.vector && $scope.vector.message) {

                var tokenIndex = $scope.vector.message.charToToken[charIndex];

                if (tokenIndex != undefined && $scope.vector.message.tokens[tokenIndex] != undefined) {

                    var tokenItem = $scope.vector.message.tokens[tokenIndex];

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
                if ($scope.vector && $scope.vector.message) {

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
                            tokens.push($scope.vector.message.tokens[tokenIndex].text);
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

        $scope.addFeature = function(tokens){
            if (tokens && tokens.length > 0){

                var key = tokens.join(" ");
                console.log("addFeature for: " + key);

                // check if it already exists
                var existingTokens = $scope.featureList[key];

                if (!existingTokens) {
                    var request = UserFeatures.add(tokens);
                    if (request) {
                        usSpinnerService.spin('vector-spinner');
                        request.then(function() {
                            usSpinnerService.stop('vector-spinner');
                            var featureId = UserFeatures.data;
                            $scope.featureList[key] = {
                                id: featureId,
                                tokens: tokens
                            };
                        });
                    }
                }
                else {
                    console.log("feature already exists: " + key);
                }

                $scope.clickStartTokenItem = undefined;
                $scope.selectedTokens = null;
                $scope.selectedTokenIndices.clear();
            }
        };

        $scope.removeFeature = function(feature){
            if (feature){
                var key = feature.tokens.join(" ");
                console.log("removeFeature for: " + key);

                // check if it already exists
                var existingTokens = $scope.featureList[key];

                if (existingTokens) {

                    var request = UserFeatures.remove(feature.id);
                    if (request) {
                        usSpinnerService.spin('vector-spinner');
                        request.then(function() {
                            usSpinnerService.stop('vector-spinner');
                            delete $scope.featureList[key];
                        });
                    }
                }
                else {
                    console.log("feature does not exist: " + key);
                }
            }
        }
    };

    ViewController.$inject = [
        '$scope',
        'TextCoder.services.Dictionary',
        'TextCoder.services.SVMResult',
        'TextCoder.services.FeatureVector',
        'TextCoder.services.UserFeatures',
        'usSpinnerService'
    ];
    module.controller('TextCoder.controllers.ViewController', ViewController);


    module.directive('datetimeFormat', function() {
      return {
        require: 'ngModel',
        link: function(scope, element, attrs, ngModelController) {
          ngModelController.$parsers.push(function(data) {
            //convert data from view format to model format
            data = moment.utc(data, "YYYY-MM-DD HH:mm:ss");
            if (data.isValid()) return data.toDate();
            else return undefined;
          });

          ngModelController.$formatters.push(function(data) {
            //convert data from model format to view format
              if (data !== undefined) return moment.utc(data).format("YYYY-MM-DD HH:mm:ss"); //converted
              return data;
          });
        }
      }
    });

    module.directive('whenScrolled', function() {
        return function(scope, element, attr) {
            var raw = element[0];

            var checkBounds = function(evt) {
                if (Math.abs(raw.scrollTop + $(raw).height() - raw.scrollHeight) < 10) {
                    scope.$apply(attr.whenScrolled);
                }

            };
            element.bind('scroll load', checkBounds);
        };
    });

    module.directive('ngEnter', function () {
        return function (scope, element, attrs) {
            element.bind("keydown keypress", function (event) {
                if(event.which === 13) {
                    scope.$apply(function (){
                        scope.$eval(attrs.ngEnter);
                    });

                    event.preventDefault();
                }
            });
        };
    });
})();
