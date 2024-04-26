import React, { Component } from "react";
import { NavLink } from "react-router-dom";
import "../../../css/MaritalDetails.css" ;
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";


class MaritalDetails extends Component {

    constructor() {
      super();
      this.state = {
        startDate: new Date()
      };
      this.handleChange = this.handleChange.bind(this);
    }

    handleChange (startDate) {
        this.setState({
          startDate
        });
    };

  render() {
    const { startDate } = this.state;
    return (
        <div className="maritalContent">
        <div className="maritalMain">
            <p>الحالة الاجتماعية        ​</p>
            <div className="maritalBody">
                <div className="maritalDetails">
                <div className="rawIcon">4</div>
                <div>عدد افراد الاسرة:​</div>
                <div className="rawIcon">1</div>
                <div>عدد الاخوة والاخوات:​</div>
                <div className="rawIcon">400</div>
                <div>دخل الاسرة الشهري:​</div>
                <div className="rawIcon">4</div>
                <div>عدد الغرف التي تشغلها الاسرة:​</div>
                <div className="rawIcon">عائلتة​</div>
                <div>وضع التلميذ العائلي يعيش مع:​</div>
                <div className="rawIcon">لا​</div>
                <div>هل التلميذ يعمل ام لا:​</div>
                <div className="rawIcon">---​</div>
                <div>مدى ملائمة الجو العام في البيت للدراسة:​</div>
                </div>
                <div className="maritalDate">
                <div className="loginbtn">السنة الدراسية</div>
                <br></br>​
                <DatePicker className="maritalDatePicker" selected={startDate} onChange={this.handleChange} />
                </div>
            </div>
            <div className="btnline">
            <NavLink className="loginbtn" to="/history">رجوع ​</NavLink>
            <NavLink className="loginbtn" to="/maritalconfirm">التالي​</NavLink>
          </div>
        </div>
      </div>
    );
  }
}

export default MaritalDetails;
