(function () {
    'use strict';

    var module = angular.module('TextCoder.services', [
        'ng.django.urls',
        'TextCoder.bootstrap',
        'ngSanitize'
    ]);

    module.factory('TextCoder.services.Dictionary', [
        '$http', 'djangoUrl',
        'TextCoder.bootstrap.dictionary',
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
    module.factory('TextCoder.services.SVMResult', [
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

    //A service for a feature vector.
    module.factory('TextCoder.services.FeatureVector', [
        '$http', 'djangoUrl', 'TextCoder.services.Dictionary',
        function scriptFactory($http, djangoUrl, Dictionary) {

            var apiUrl = djangoUrl.reverse('vector');

            var FeatureVector = function () {
                var self = this;
                self.data = undefined;
            };

            angular.extend(FeatureVector.prototype, {
                load: function (message_id) {
                    var self = this;

                    var request = {
                        params: {
                            dictionary_id: Dictionary.id,
                            message_id: message_id
                        }
                    };
                    return $http.get(apiUrl, request)
                        .success(function (data) {
                            self.data = data;
                        });

                }
            });

            return new FeatureVector();
        }
    ]);

    //A service for user defined features.
    module.factory('TextCoder.services.UserFeatures', [
        '$http', 'djangoUrl', 'TextCoder.services.Dictionary',
        function scriptFactory($http, djangoUrl, Dictionary) {

            var listApiUrl = djangoUrl.reverse('feature_list');

            var UserFeatures = function () {
                var self = this;
                self.data = undefined;
            };

            angular.extend(UserFeatures.prototype, {
                load: function () {
                    var self = this;

                    var request = {
                        params: {
                        }
                    };
                    return $http.get(listApiUrl, request)
                        .success(function (data) {
                            self.data = data;
                        });

                }
            });

            angular.extend(UserFeatures.prototype, {
                add: function (tokens) {
                    var self = this;

                    var request = {
                        dictionary: Dictionary.id,
                        token_list: tokens

                    };

                    return $http.post(listApiUrl, request)
                        .success(function (data) {
                            self.data = data;
                        });

                }
            });

            angular.extend(UserFeatures.prototype, {
                remove: function (feature) {
                    var self = this;

                    var request = {
                        params: {
                        }
                    };

                    var itemApiUrl = djangoUrl.reverse('feature', { 'feature_id' : feature.id });
                    return $http.delete(itemApiUrl, request)
                        .success(function (data) {
                            self.data = data;
                        });

                }
            });

            return new UserFeatures();
        }
    ]);

})();
