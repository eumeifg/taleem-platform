import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import App from './App';

// export class EnrollmentDashboard {
//   constructor() {
//   }
//
//   render
// }
// ReactDOM.render(
//   <React.StrictMode>
//     <App />
//   </React.StrictMode>,
//   document.getElementById('root')
// );

export class EnrollmentDashboard {
    constructor() {
        ReactDOM.render(
            <App />,
            document.getElementById('root'),
        );
    }
}

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
