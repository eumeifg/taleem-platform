import React, { Component } from "react";
import "../../../css/Details.css"
import {
  NavLink
} from "react-router-dom";

class Details extends Component {
  render() {
    return (
      <div className="detContent">
        <div className="detMain">
            <div className="detValue">علي محمد احمد​</div>
            <div className="detId">الاسم الرباعي واللقب:</div>
            <div className="detValue">محمد احمدعلي​</div>
            <div className="detId">اسم ولي الامر :​</div>
            <div className="detValue">مريم محمد حسن​</div>
            <div className="detId">اسم الام الثلاثي : ​</div>
            <div className="detValue">محامي</div>
            <div className="detId">مهنة الاب وعنوانه الوضيفي :​</div>
            <div className="detValue">المنصور-محله302- زقاق 3-دار 10 ​</div>
            <div className="detId">عنوان السكن : ​</div>
            <div className="detValue">2017594618347​</div>
            <div className="detId">رقم هوية الاحوال المدنية :​</div>
            <div className="detValue">بغداد​</div>
            <div className="detId">مسقط الرأٍس :​</div>
            <div className="detValue">بغداد​</div>
            <div className="detId">التولد :​</div>
            <div className="detValue">عراقي​</div>
            <div className="detId">الجنسية :​</div>
            <div className="detValue">مسلم​</div>
            <div className="detId">الديانة :​</div>
            <div className="detValue">2/8/2020​</div>
            <div className="detId">تاريخ دخول المدرسة :​</div>
            <div className="detValue">125687​</div>
            <div className="detId">رقم القبول في القيد العام: ​</div>
            <div className="detbuttonLine">
              <div></div>
              <NavLink className="detloginButtonTag" to="/acknowledgement">رجوع ​</NavLink>
              <NavLink className="detloginButtonTag" to="/examcard">التالي​</NavLink>
          </div>
        </div>
      </div>
    );
  }
}

export default Details;
