import React, { Component } from "react";
import "../../../css/History.css";
import { NavLink } from "react-router-dom";

class History extends Component {
  render() {
    return (
        <div className="historyContent">
        <div className="historyMain">
           <p>المدارس والكليات التي التحق بها التلميذ /الطالب خلال سنوات الدراسة​</p>
           <div className="rawFinish">
                  <div className="rawIcon">المتميزين​</div>
                  <div>اسم المدرسة او الكلية او المعهد:​</div>
                  <div className="rawIcon">بغداد​</div>
                  <div>المحافظة:​</div>
                  <div className="rawIcon">المحافظة:​</div>
                  <div>تاريخ الالتحاق: ​</div>
                  <div className="rawIcon">126548963​</div>
                  <div>رقمة في سجل القيد:​</div>
                  <div className="rawIcon">/</div>
                  <div>تاريخ الانتقال الى مدرسة اخرى:​</div>
                  <div className="rawIcon">لايوجد​</div>
                  <div>الملاحظات:​</div>
            </div>
            <div className="btnline">
            <NavLink className="loginbtn" to="/rawdata">رجوع ​</NavLink>
            <NavLink className="loginbtn" to="/maritaldetails">التالي​</NavLink>
          </div>
        </div>
      </div>
    );
  }
}

export default History;
