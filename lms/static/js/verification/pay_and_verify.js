/**
 * Entry point for the payment/verification flow.
 * This loads the base view, which in turn loads
 * subviews for each step in the flow.
 *
 * We pass some information to the base view
 * using "data-" attributes on the parent div.
 * See "pay_and_verify.html" for the exact attribute names.
 *
 */
var edx = edx || {};

(function($, _) {
    'use strict';
    var errorView,
        $el = $('#pay-and-verify-container');

    edx.verify_student = edx.verify_student || {};

    // Initialize an error view for displaying top-level error messages.
    errorView = new edx.verify_student.ErrorView({
        el: $('#error-container')
    });

    // Initialize the base view, passing in information
    // from the data attributes on the parent div.
    //
    // The data attributes capture information that only
    // the server knows about, such as the course and course mode info,
    // full URL paths to static underscore templates,
    // and some messaging.
    //
    return new edx.verify_student.PayAndVerifyView({
        errorModel: errorView.model,
        displaySteps: $el.data('display-steps'),
        currentStep: $el.data('current-step'),
        stepInfo: {
            'intro-step': {
                isActive: $el.data('is-active'),
                platformName: $el.data('platform-name'),
                requirements: $el.data('requirements')
            },
            'face-photo-step': {
                platformName: $el.data('platform-name'),
                captureSoundPath: $el.data('capture-sound')
            },
            'id-photo-step': {
                platformName: $el.data('platform-name'),
                captureSoundPath: $el.data('capture-sound')
            },
            'review-photos-step': {
                fullName: $el.data('full-name'),
                platformName: $el.data('platform-name')
            },
            'enrollment-confirmation-step': {
                platformName: $el.data('platform-name')
            }
        }
    }).render();
}(jQuery, _));
