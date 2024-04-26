import React, { Component } from "react";
import "../../../css/Examcard.css"
import {
  NavLink
} from "react-router-dom";
import examid from "../assets/examid.PNG";

class Examcard extends Component {
  render() {
    return (
        <div className="examContent">
        <div className="examMain">
           <div className="examHeader">
               <div>
                   <p>وزارة التربية ​</p>
                   <p>مديرية التقويم والتوجية التربوي ​</p>
               </div>
               <img src={examid}></img>
               <div>
                   <p>جمهورية العراق​</p>
                   <p>المديرية العامة للتقويم والامتحانات​</p>
               </div>
           </div>
           <div className="examStudent">
             <p>علي محمد احمد​</p>
             <p>الاسم الثلاثي : ​</p>
           </div>
           <div className="examNotes">
           ملاحظات مهمة : ​
           <br></br>
يرجى الاطلاع على دليل البطاقة المدرسية قبل الشروع بملئ صفحاتها​
<br></br> يرجى التأكد من صحة البيانات ودقتها قبل تدوينها في الحقول المخصص لها​

<br></br> تعتبر البيانات المدونه في هذه البطاقة سرية ولا يجوز تداولها الا لأغراض التقويم والوجية التربوي​
          </div>
          <div className="buttonClass">
          <NavLink className="examloginButtonTag" to="/rawdata">التالي​</NavLink>
          </div>
        </div>
      </div>
    );
  }
}

export default Examcard;
