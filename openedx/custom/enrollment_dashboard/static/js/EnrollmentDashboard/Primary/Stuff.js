import React, { Component } from "react";
import '../../../css/Stuff.css';
import {
  NavLink
} from "react-router-dom";

class Stuff extends Component {
  render() {
    return (
      <div className="stuffcontent">
        <div className="stuffmain">
          <div className="detail">المتميزين</div>
          <div className="label">ادارة :​</div>
          <div className="detail">علي محمد احمد​</div>
          <div className="label">الاسم الرباعي واللقب:​</div>
          <div className="detail">بغداد/المنصور​</div>
          <div className="label">العنوان :​</div>
          <div className="detail">7/2/2017​</div>
          <div className="label">تاريخ التولد :​</div>
          <div className="detail">84456872356​</div>
          <div className="label">رقم القبول :​</div>
          <div className="detail">1150/2/8/2020​</div>
          <div className="label">رقم الوثيقة وتاريخها :​</div>
          <div className="buttonLine">
            <div></div>
            <NavLink className="loginButtonTag" to="/">رجوع ​</NavLink>
            <NavLink className="loginButtonTag" to="/acknowledgement">التالي​</NavLink>
          </div>
        </div>
      </div>
    );
  }
}

export default Stuff;
