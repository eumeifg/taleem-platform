import React, { Component } from "react";
import '../../../css/Home.css';
import {
  NavLink
} from "react-router-dom";

class Home extends Component {
  render() {
    return (
      <div  className="home">
        <div className="login">
          <div className="hometitle"> تسجيل دخول​ </div>
          <div className="label">
           <div></div>
            <input
            type='text'
            name='username'
            ></input>
             <label>اسم المستخدم ​</label>
          </div>
          <div className="label">
          <div></div>
            <input
            type='password'
            name='username'
            ></input>
            <label> الرقم السري ​ </label>
          </div>
          <div className="note">
          اذا لم يكن لديك حساب اضغط للتسجيل​
          </div>
          <div className="buttonClass">
            <div></div>

            <NavLink className="loginButtonTag" to="/stuff">التالي</NavLink>

          </div>
        </div>
      </div>
    );
  }
}

export default Home;
