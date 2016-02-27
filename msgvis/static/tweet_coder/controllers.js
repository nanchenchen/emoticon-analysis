(function () {
    'use strict';


    var module = angular.module('TweetCoder.controllers', [
        'TweetCoder.services',
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
        'TweetCoder.services.Dictionary'
    ];
    module.controller('TweetCoder.controllers.DictionaryController', DictionaryController);

    var ViewController = function ($scope, $timeout, Dictionary, SVMResult, usSpinnerService) {

        $scope.spinnerOptions = {
            radius: 20,
            width: 6,
            length: 10,
            color: "#000000"
        };

        $scope.currentMessage = undefined;
        $scope.currentLabel = undefined;
        $scope.isCurrentMessageAmbiguous = false;
        $scope.codes = undefined;
        $scope.submittedLabels = undefined;
        $scope.displayedLabels = [];

        $scope.load = function(){
            var request = SVMResult.load(Dictionary.id);
            if (request) {
                usSpinnerService.spin('table-spinner');
                request.then(function() {
                    usSpinnerService.stop('table-spinner');
                    $scope.codes = SVMResult.data.codes;
                    $scope.submittedLabels = [];

                    // Fake data for now
                    for (var i = 0; i < 100; i++){
                        var codeIndex = Math.floor(Math.random() * ($scope.codes.length + 1));
                        var ambiguous = Math.random() < 0.5;
                        var label = {
                            text: i + "@HopeForBoston: R.I.P. to the 8 year-old girl who died in Bostons explosions, while running for the Sandy @PeytonsHead RT for spam please",
                            ambiguous: ambiguous.toString()
                        };

                        $scope.codes.forEach(function(c) {
                            label[c.text] = (c.index == codeIndex ? "X" : "");
                        });

                        $scope.submittedLabels.push(label);
                    }
                });
            }
        };

        $scope.getMessage = function() {
            console.log("getMessage");
            usSpinnerService.spin('label-spinner');

            $timeout(function(){
                console.log("gotMessage");
                usSpinnerService.stop('label-spinner');
                $scope.currentMessage = (new Date()) + "@HopeForBoston: R.I.P. to the 8 year-old girl who died in Bostons explosions, while running for the Sandy @PeytonsHead RT for spam please";
                $scope.selectLabel(null);
                $scope.isCurrentMessageAmbiguous = false;
            }, 1000);
        };

        $scope.selectLabel = function(label){
            console.log("selectLabel " + label);
            $scope.currentLabel = label;
        };

        $scope.submitLabel = function(){
            console.log("submitLabel");
            $scope.getMessage();
        };

        // load the svm results
        $scope.load();

        // fetch a message to label
        $scope.getMessage();
    };

    ViewController.$inject = [
        '$scope',
        '$timeout',
        'TweetCoder.services.Dictionary',
        'TweetCoder.services.SVMResult',
        'usSpinnerService'
    ];
    module.controller('TweetCoder.controllers.ViewController', ViewController);


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
