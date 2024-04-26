/* global gettext */
/* eslint react/no-array-index-key: 0 */

import PropTypes from 'prop-types';
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';

var $ = require('jquery');
require('cms/js/main')

export function CourseOrLibraryListing(props) {
  const allowReruns = props.allowReruns;
  const linkClass = props.linkClass;
  const idBase = props.idBase;
  const isAdmin = props.isAdmin;

  const [courses, setCourses] = useState(props.items);

  const courseSearch = function (course, searchStr) {
      searchStr = searchStr.toLowerCase();
      var key = (course.course_key || course.library_key || '').toLowerCase();
      var display_name = (course.display_name || '').toLowerCase();
      var org = (course.org || '').toLowerCase();

      return (
          display_name.includes(searchStr) ||
          key.includes(searchStr) ||
          org.includes(searchStr)
      );
  };

  useEffect(() => {
      $('#search').on('keyup change', function(e){
          setCourses(
              courses.filter(course => courseSearch(course, e.target.value))
          )
      });
    return () => $('#search').off('keyup change');
  }, []);

  const getDeleteQuestionBankHandler = function (deleteLink, associatedWithTimedExam) {
      return function (event) {
          event.preventDefault();
          var jqueryModalID = '';

          if (associatedWithTimedExam) {
            jqueryModalID = '#questionBankDeleteDisable';
          } else {
            jqueryModalID = '#questionBankDeleteConfirmation';
          }

          $(jqueryModalID).jqueryModal({
            escapeClose: false,
            clickClose: false,
            showClose: false
          });

          $('#confirm-delete-question-bank').off('click').on('click', function () {
              $.postJSON(deleteLink, function (data){
                window.location = data.url;
              });

          });
      };
  }

    const getArchiveCourseHandler = function (archiveLink) {
      return function (event) {
          event.preventDefault();
          var jqueryModalID = '#courseArchivalConfirmation';

          $(jqueryModalID).jqueryModal({
            escapeClose: false,
            clickClose: false,
            showClose: false
          });

          $('#confirm-archive-course').off('click').on('click', function () {
              $.postJSON(archiveLink, function (data){
                window.location = data.url;
              });

          });
      };
  }

  return (
    <ul className="list-courses">
      {
        courses.map((item, i) =>
          (
            <li key={i} className="course-item" data-course-key={item.course_key}>
              <a className={linkClass} href={item.url}>
                <h3 className="course-title" id={`title-${idBase}-${i}`}>{item.display_name}</h3>
                <div className="course-metadata">
                  <span className="course-org metadata-item">
                    <span className="label">{gettext('Organization:')}</span>
                    <span className="value">{item.org}</span>
                  </span>
                  <span className="course-num metadata-item">
                    <span className="label">{gettext('Course Number:')}</span>
                    <span className="value">{item.number}</span>
                  </span>
                  { item.run &&
                  <span className="course-run metadata-item">
                    <span className="label">{gettext('Course Run:')}</span>
                    <span className="value">{item.run}</span>
                  </span>
                  }
                  { item.can_edit === false &&
                  <span className="extra-metadata">{gettext('(Read-only)')}</span>
                  }
                </div>
              </a>
              { item.lms_link && item.rerun_link &&
              <ul className="item-actions course-actions">
                { allowReruns &&
                <li className="action action-rerun">
                  <a
                    href={item.rerun_link}
                    className="button rerun-button"
                    aria-labelledby={`re-run-${idBase}-${i} title-${idBase}-${i}`}
                    id={`re-run-${idBase}-${i}`}
                  >{gettext('Re-run Course')}</a>
                </li>
                }
                <li className="action action-view">
                  <a
                    href={item.lms_link}
                    rel="external"
                    className="button view-button"
                    aria-labelledby={`view-live-${idBase}-${i} title-${idBase}-${i}`}
                    id={`view-live-${idBase}-${i}`}
                  >{gettext('View Live')}</a>
                </li>
                { isAdmin &&
                <li className="action action-view time-exam-action">
                  <a
                    style={{cursor: 'pointer'}}
                    onClick={getArchiveCourseHandler(item.archive_link)}
                    rel="external"
                    href={'#archive-course'}
                    className="button view-button archive-course time-exam-view-button"
                    aria-labelledby={`archive-${idBase}-${i} title-${idBase}-${i}`}
                    id={`archive-${idBase}-${i}`}
                  ><span className="icon fa fa-trash" aria-hidden="true"></span></a>
                </li>
                }
              </ul>
              }
              { item.allow_actions && item.delete_question_bank &&
              <ul className="item-actions course-actions">
                <li className="action action-view">
                    <a
                        style={{cursor: 'pointer'}}
                        onClick={getDeleteQuestionBankHandler(item.delete_question_bank, item.associated_with_timed_exam)}
                        rel="external"
                        href={'#delete-question-bank'}
                        className="button view-button delete-question-bank"
                        aria-labelledby={`delete-${idBase}-${i} title-${idBase}-${i}`}
                        id={`delete-${idBase}-${i}`}
                      >{gettext('Delete')}</a>
                </li>
              </ul>
              }
            </li>
          ),
        )
      }
    </ul>
  );
}

CourseOrLibraryListing.propTypes = {
  allowReruns: PropTypes.bool.isRequired,
  idBase: PropTypes.string.isRequired,
  items: PropTypes.arrayOf(PropTypes.object).isRequired,
  linkClass: PropTypes.string.isRequired,
};
