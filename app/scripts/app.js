'use strict';

/**
 * @ngdoc overview
 * @name journeyApp
 * @description
 * # journeyApp
 *
 * Main module of the application.
 */
angular
  .module('journeyApp', [
    'ngAnimate',
    'ngCookies',
    'ngResource',
    'ngRoute',
    'ngSanitize',
    'ngTouch'
  ])
  .config(function ($routeProvider) {
    $routeProvider
      .when('/', {
        templateUrl: 'views/main.html',
        controller: 'MainCtrl',
        controllerAs: 'main'
      })
      .when('/about', {
        templateUrl: 'views/about.html',
        controller: 'AboutCtrl',
        controllerAs: 'about'
      })
      .when('/check', {
        templateUrl: 'views/check.html',
        controller: 'CheckCtrl',
        controllerAs: 'check'
      })
      .otherwise({
        redirectTo: '/'
      });
  });
