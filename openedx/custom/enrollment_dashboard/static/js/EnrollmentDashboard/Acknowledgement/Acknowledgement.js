import React, { Component } from "react";
import book from "../assets/book.PNG";
import "../../../css/Acknowledgement.css";
import {
  NavLink
} from "react-router-dom";

class Acknowledgement extends Component {
  render() {
    return (
      <div className="ackcontent">
        <div className="ackmain">
          <div className="headContent">
          <div className="valueBox">2/8/2020​</div>
          <div>التاريخ​</div>
          <img src={book}></img>
          <div className="valueBox">المتميزين​</div>
          <div>ادارة مدرسة ​</div>
        </div>
          <div className="ackTitle">تعهد </div>
          <div className="ackBody">
          أني ولي امر التلميذعلي محمد​اتعهد بصحة المعلومات عن  عمر ولدي المثبت في المستمسكات المقدمة اليكم وخاصة هوية الأحوال المدنية المرقمة 20214566 الصادرة من دائرة الاحوال المدنيةالكرخوفي حال التزوير سأتحمل كافة التبعات القانونية واقامة الدعوات الجزائية بحقي استناداً الى كتاب التعليم الابتدائي المرقم (4567) في 14/6/2019​
          </div>
          <div className="ackSign"> موافق على الشروط ​ </div>
          <div className="ackbuttonLine">
          <div></div>
            <NavLink className="loginButtonTag" to="/stuff">رجوع ​</NavLink>
            <NavLink className="loginButtonTag" to="/details">التالي​</NavLink>
          </div>
        </div>
      </div>
    );
  }
}

export default Acknowledgement;
