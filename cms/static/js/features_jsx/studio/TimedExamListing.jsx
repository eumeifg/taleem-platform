/* global gettext */
/* eslint react/no-array-index-key: 0 */

import PropTypes from 'prop-types';
import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';

var $ = require('jquery');
require('cms/js/main')

export function TimedExamListing(props) {
  const linkClass = props.linkClass;
  const idBase = props.idBase;
  const [timedExams, setTimedExams] = useState(props.items);

  const timedExamSearch = function (timedExam, searchStr) {
      searchStr = searchStr.toLowerCase();
      var key = (timedExam.course_key || timedExam.library_key || '').toLowerCase();
      var display_name = (timedExam.display_name || '').toLowerCase();

      return (
          display_name.includes(searchStr) ||
          key.includes(searchStr)
      );
  };

  useEffect(() => {
      $('#search').on('keyup change', function(e){
          setTimedExams(
              timedExams.filter(timedExam => timedExamSearch(timedExam, e.target.value))
          )
      });
    return () => $('#search').off('keyup change');
  }, []);


  const getDeleteTimedExamHandler = function (deleteLink, hasEnrolledStudent) {
      return function (event) {
          event.preventDefault();
          var jqueryModalID = '';

          if (hasEnrolledStudent) {
            jqueryModalID = '#timedExamDeleteDisable';
          } else {
            jqueryModalID = '#timedExamDeleteConfirmation';
          }

          $(jqueryModalID).jqueryModal({
            escapeClose: false,
            clickClose: false,
            showClose: false
          });

          $('#confirm-delete').off('click').on('click', function () {
              $.postJSON(deleteLink, function (data){
                window.location = data.url;
              });

          });
      };
  }

  const generateEnrollmentCodeHandler = function (generateNewCodeURL, enrollmentCode) {
      return function (event) {
          event.preventDefault();
          if (enrollmentCode) {
            $("#enrollmentCodeExist").text(enrollmentCode);
            $("#enrollmentCodeExist").removeClass('hidden');
            $("#enrollmentCodeNotExist").addClass('hidden');
            $("#copy-button").removeClass('hidden');
          } else {
            $("#enrollmentCodeExist").addClass('hidden');
            $("#enrollmentCodeNotExist").removeClass('hidden');
            $("#copy-button").addClass('hidden');
          }

          $("#enrollmentCode").jqueryModal({
            escapeClose: false,
            clickClose: false,
            showClose: false
          });

          $('#generate-code').off('click').on('click', function () {
              $.postJSON(generateNewCodeURL, function (data){
                if (data.status === 200) {
                    $("#enrollmentCodeExist").text(data.enrollment_code);
                    $("#enrollmentCodeExist").removeClass('hidden');
                    $("#enrollmentCodeNotExist").addClass('hidden');
                } else {
                    $("#enrollmentCodeExist").addClass('hidden');
                    $("#enrollmentCodeNotExist").removeClass('hidden');
                    alert("Something bad happened");
                }

                if ($("#enrollmentCodeExist").hasClass('hidden')) {
                    $("#copy-button").addClass('hidden');
                } else {
                    $("#copy-button").removeClass('hidden');
                }
              });
          });

          $('#copy-button').off('click').on('click', function () {
              var copyText = $("#enrollmentCodeExist").text();
              console.log(copyText);
              navigator.clipboard.writeText($("#enrollmentCodeExist").text());
              $("#copy-button").addClass('hidden');
              $("#close-button").removeClass('hidden');
          });
      };
  }

  const generateEnrollmentPasswordHandler = function (generateNewPasswordURL, enrollmentPassword, isPublic, examEnrollmentURL) {
      return function (event) {
          event.preventDefault();
          if (isPublic) {
              $("#timedExamIsPublic").removeClass('hidden');
              $("#generate-password").addClass('hidden');
              $('#enrollmentPasswordAndURL').text('This is the public timed exam you can not create the enrollment URL for this timed exam.');
              $("#enrollmentPassword").jqueryModal({
                escapeClose: false,
                clickClose: false,
                showClose: false
              });
              return;
          } else {
              $("#timedExamIsPublic").addClass('hidden');
              $('#enrollmentPasswordAndURL').text('Please click the generate button to show enrollment URL and password.');
          }

          if (enrollmentPassword) {
            $("#timedExamIsPublic").addClass('hidden');
            $("#generate-password").addClass('hidden');
            $("#enrollmentPasswordAndURL")
              .empty()
              .append('<p>Here are the URL and password for enrollment in the timed exam.</p>')
              .append('<ul style="list-style: circle;"><li><a href="' + examEnrollmentURL + '">' + examEnrollmentURL + '</a></li><li> ' + enrollmentPassword + '</li><ul>');
          } else {
            $("#timedExamIsPublic").addClass('hidden');
            $("#enrollmentPasswordAndURL").removeClass('hidden');
            $("#generate-password").removeClass('hidden');
          }

          $("#enrollmentPassword").jqueryModal({
            escapeClose: false,
            clickClose: false,
            showClose: false
          });

          $('#generate-password').off('click').on('click', function () {
              $.postJSON(generateNewPasswordURL, function (data){
                enrollmentPassword = data.enrollment_password;

                if (data.status === 200) {
                    $("#timedExamIsPublic").addClass('hidden');
                    $("#generate-password").addClass('hidden');

                    $("#enrollmentPasswordAndURL")
                      .empty()
                      .append('<p>Here are the URL and password for enrollment in the timed exam.</p>')
                      .append('<ul style="list-style: circle;"><li><a href="' + examEnrollmentURL + '">' + examEnrollmentURL + '</a></li><li> ' + enrollmentPassword + '</li><ul>');
                } else {
                    $("#timedExamIsPublic").addClass('hidden');
                    $("#enrollmentPasswordAndURL").addClass('hidden');
                    $("#generate-password").removeClass('hidden');
                    alert("Something bad happened");
                }
              });
          });
      };
  }

  return (
    <ul className="list-courses list-timed-exams">
      {
        timedExams.map((item, i) =>
          (
            <li key={i} className="course-item" data-course-key={item.course_key}>
              <a
                  className={linkClass}
                  href={item.has_enrollments ? '#' : item.url}
                  style={item.has_enrollments ? { 'pointer-events': 'none', 'cursor': 'default' } : {} }
              >
                <h3 className="course-title" id={`title-${idBase}-${i}`}>{item.display_name}</h3>
                <div className="course-metadata">
                  <table width="100%">
                    <thead>
                      <tr>
                        <th>{gettext('Start Date')}</th>
                        <th>{gettext('Deadline')}</th>
                        <th>{gettext('Duration')}</th>
                        <th>{gettext('Proctored')}</th>
                        <th>{gettext('Round')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td>{item.start}</td>
                        <td>{item.end}</td>
                        <td>{item.duration}</td>
                        <td>{item.proctored}</td>
                        <td>{item.round}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </a>
              { item.report_link &&
              <ul className="item-actions course-actions time-exam-action">
                <li className="action action-view">
                  <a
                    href={item.report_link}
                    rel="external"
                    className="button view-button time-exam-view-button"
                    aria-labelledby={`view-report-${idBase}-${i} title-${idBase}-${i}`}
                    id={`view-report-${idBase}-${i}`}
                  >{gettext('Preview')}</a>
                </li>

                <li className="action action-view time-exam-action">
                  <a
                    style={{cursor: 'pointer'}}
                    onClick={generateEnrollmentCodeHandler(item.generate_enrollment_code_url, item.enrollment_code)}
                    href={'#enrollment-code-view'}
                    rel="external"
                    className="button view-button time-exam-view-button enrollment-code"
                    aria-labelledby={`view-report-${idBase}-${i} title-${idBase}-${i}`}
                    id={`view-report-${idBase}-${i}`}
                  >{gettext('Enrollment Code')}</a>
                </li>
                <li className="action action-view time-exam-action">
                  <a
                    style={{cursor: 'pointer'}}
                    onClick={generateEnrollmentPasswordHandler(item.generate_enrollment_password_url, item.enrollment_password, item.is_public, item.exam_enrollment_url)}
                    href={'#enrollment-password-view'}
                    rel="external"
                    className="button view-button time-exam-view-button enrollment-password"
                    aria-labelledby={`view-report-${idBase}-${i} title-${idBase}-${i}`}
                    id={`view-report-${idBase}-${i}`}
                  >{gettext('Generate Enrollment URL')}</a>
                </li>

                <li className="action action-view time-exam-action">
                  <a
                    href={item.management_link}
                    rel="external"
                    className="button view-button time-exam-management-button"
                    aria-labelledby={`view-management-${idBase}-${i} title-${idBase}-${i}`}
                    id={`view-management-${idBase}-${i}`}
                  >{gettext('Management')}</a>
                </li>

                <li className="action action-view time-exam-action">
                    <a
                        href={item.enrollment_link}
                        rel="external"
                        className="button view-button time-exam-view-button"
                        aria-labelledby={`enroll-${idBase}-${i} title-${idBase}-${i}`}
                        id={`enroll-${idBase}-${i}`}
                      >{gettext('Enroll')}</a>
                </li>
                <li className="action action-view time-exam-action">
                    <a
                        style={{cursor: 'pointer'}}
                        onClick={getDeleteTimedExamHandler(item.delete_link, item.has_enrolled_students)}
                        rel="external"
                        href={'#delete-timed-exam'}
                        className="button view-button delete-timed-exam time-exam-view-button"
                        aria-labelledby={`delete-${idBase}-${i} title-${idBase}-${i}`}
                        id={`delete-${idBase}-${i}`}
                      ><span class="icon fa fa-trash" aria-hidden="true"></span></a>
                </li>
                <li className="action action-view time-exam-action">
                  <a
                    style={item.is_hidden ? {cursor: 'pointer'} : {display: 'none'} }
                    href={item.unhide_link}
                    className="button view-button time-exam-unhide-button"
                    aria-labelledby={`view-exam_unhide-${idBase}-${i} title-${idBase}-${i}`}
                    id={`view-report-${idBase}-${i}`}
                  >{gettext('Unarchive')}</a>
                </li>
              </ul>
              }
            </li>
          ),
        )
      }
    </ul>
  );
};

TimedExamListing.propTypes = {
  idBase: PropTypes.string.isRequired,
  items: PropTypes.arrayOf(PropTypes.object).isRequired,
  linkClass: PropTypes.string.isRequired,
};

