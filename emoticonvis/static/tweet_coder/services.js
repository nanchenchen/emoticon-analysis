(function () {
    'use strict';

    var module = angular.module('TweetCoder.services', [
        'ng.django.urls',
        'TweetCoder.bootstrap',
        'ngSanitize'
    ]);

    module.factory('TweetCoder.services.Dictionary', [
        '$http', 'djangoUrl',
        'TweetCoder.bootstrap.dictionary',
        function datasetFactory($http, djangoUrl, dictionaryId) {
            var apiUrl = djangoUrl.reverse('dictionary');

            var Dictionary = function () {
                this.id = dictionaryId
            };

            var request = {
                params: {
                    id: dictionaryId
                }
            };
            $http.get(apiUrl, request)
                .success(function (data) {
                    angular.extend(Dictionary.prototype, data);
                });

            return new Dictionary();

        }
    ]);


    //A service for svm results.
    module.factory('TweetCoder.services.SVMResult', [
        '$rootScope', '$http', 'djangoUrl',
        function similarityGraphFactory($rootScope, $http, djangoUrl) {

            var apiUrl = djangoUrl.reverse('svm');

            var SVMResult = function () {
                var self = this;
                self.data = undefined;
                self.dist_scale = d3.scale.linear();

            };

            angular.extend(SVMResult.prototype, {

                load: function (dictionary_id) {
                    var self = this;

                    var request = {
                        params: {
                            dictionary_id: dictionary_id
                        }
                    };

                    return $http.get(apiUrl, request)
                        .success(function (data) {
                            self.data = data.results;
                            self.calc_dist();
                        });

                },
                calc_dist: function(){
                    var self = this;
                    if (self.data){
                        var domain = [0, 0];
                        self.data.codes.forEach(function(code){
                            if (code.train_count > domain[1])
                                domain[1] = code.train_count;
                        });
                        self.dist_scale.domain(domain);
                        return true;
                    }
                    return false;
                }
            });

            return new SVMResult();
        }
    ]);

})();
