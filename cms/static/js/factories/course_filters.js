define(
  ['domReady', 'jquery', 'gettext', 'edx-ui-toolkit/js/utils/string-utils', 'dataTables'],
  function(domReady, $, gettext, StringUtils) {
      'use strict';

      var addNewCourseFilter = function(e) {
          e.preventDefault();
          $('#newFilterButton').addClass('is-disabled').attr('aria-disabled', true);
          $('.wrapper-course-filter').addClass('is-shown');
      };

      function getCategoryValues(categoryID) {
          if (categoryID === '') {
              $('#field-filter-value').attr('hidden', true);
              $('#selectFilterValue').attr('required', false);
          } else {
              $.getJSON(
                '/search/filters/' + categoryID
              ).done(function(data) {
                  var filters = data.filters;
                  $('#selectFilterValue').empty();

                  if (filters.length > 0) {
                      filters.forEach(function(filter) {
                          var option = document.createElement('option');
                          if (document.documentElement.lang === 'ar') {
                              option.text = filter.value_in_arabic;
                          } else {
                              option.text = filter.value;
                          }
                          option.value = filter.id;
                          $('#selectFilterValue')[0].appendChild(option);
                      });
                  } else {
                      $('#fieldAddNewFilter').removeAttr('hidden').addClass('required');
                      $('#addNewFilter').attr('required', true);
                      $('#fieldAddNewArabicFilter').removeAttr('hidden').addClass('required');
                      $('#addNewArabicFilter').attr('required', true);
                  }

                  var addNewOption = document.createElement('option');
                  addNewOption.text = gettext('Add New Filter');
                  addNewOption.value = 'add_new';
                  $('#selectFilterValue')[0].appendChild(addNewOption);

                  $('#field-filter-value').removeAttr('hidden');
                  $('#selectFilterValue').attr('required', true);
              }).fail(function(jqXHR, textStatus, errorThrown) {
                  var reason = errorThrown;
                  if (jqXHR.responseText) {
                      try {
                          var detailedReason = $.parseJSON(jqXHR.responseText).ErrMsg;
                          if (detailedReason) {
                              reason = detailedReason;
                          }
                      } catch (e) {}
                  }
                  console.log(reason);
              });
          }
      }

      var getFilterCategoryValue = function() {
          var filterCategory = $('#selectFilterCategory').val();
          getCategoryValues(filterCategory);
      };

      var handleFilterChange = function() {
          var filterValue = $('#selectFilterValue').val();
          if (filterValue === 'add_new') {
              $('#fieldAddNewFilter').removeAttr('hidden').addClass('required');
              $('#addNewFilter').attr('required', true);
              $('#fieldAddNewArabicFilter').removeAttr('hidden').addClass('required');
              $('#addNewArabicFilter').attr('required', true);
          } else {
              $('#fieldAddNewFilter').attr('hidden', true).removeClass('required');
              $('#addNewFilter').removeAttr('required');
              $('#fieldAddNewArabicFilter').attr('hidden', true).removeClass('required');
              $('#addNewArabicFilter').removeAttr('required');
          }
      };

      var onReady = function() {
          $('#newFilterButton').bind('click', addNewCourseFilter);
          $('#selectFilterCategory').bind('change', getFilterCategoryValue);
          $('#selectFilterValue').bind('change', handleFilterChange);

          $('#courseFilterListTable').DataTable({
            language: {
                url: (typeof datatablesLangPath !== 'undefined') ? datatablesLangPath : "",
            },
          });
      };

      domReady(onReady);

      return {
          onReady: onReady
      };
  }
);
