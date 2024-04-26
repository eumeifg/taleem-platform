import React, { Component } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { NavLink } from "react-router-dom";
import "../../../css/MaritalConfirm.css";


class MaritalConfirm extends Component {
  constructor(){
    super();
    this.state = {
      startDate: new Date()
    };
    this.handleChange = this.handleChange.bind(this);
  }


  handleChange(startDate) {
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
                <div className="rawIcon">70سم​</div>
                <div>الطول:​</div>
                <div className="rawIcon">25كغم​</div>
                <div>درجة البصر:​</div>
                <div className="marData">
                    <div className="rawIcon"> 6/6​ </div>
                    <div> بالفحص الطبي​ </div>
                    <div className="rawIcon"> 6/6​ </div>
                    <div>بالملاحظة​</div>
                </div>
                <div>درجة البصر:​</div>
                <div className="marData">
                    <div className="rawIcon"> 10​ </div>
                    <div>بالفحص الطبي​</div>
                    <div className="rawIcon"> 10 </div>
                    <div>بالملاحظة​</div>
                </div>
                <div>درجة السمع:​</div>
                <div className="marData">
                    <div className="rawIcon"> 10​ </div>
                    <div>غير سليم​</div>
                    <div className="rawIcon"> نعم​ </div>
                    <div>سليم​</div>
                </div>
                <div>النطق:​</div>
                <div className="rawIcon">لايوجد​</div>
                <div>العاهات الجسمية:​</div>
                <div className="rawIcon">نعم​</div>
                <div>هل اكمل التلقيحات المطلوبة:​</div>
                <div className="rawIcon">10</div>
                <div>الحالة الصحية العامة :​</div>

                </div>
                <div className="maritalDate">
                <div className="loginbtn">   السنة الدراسية​</div>
                <br></br>​
                <DatePicker className="maritalDatePicker" selected={startDate} onChange={this.handleChange} />
                </div>
            </div>
            <div className="btnline">
            <NavLink className="loginbtnTag" to="/maritaldetails">رجوع ​</NavLink>
            <NavLink className="loginbtnTag" to="/academics">التالي​</NavLink>
            </div>
        </div>
      </div>
    );
  }
}

export default MaritalConfirm;
