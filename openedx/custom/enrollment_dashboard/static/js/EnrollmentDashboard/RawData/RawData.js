import React, { Component } from "react";
import { NavLink } from "react-router-dom";
import child from "../assets/child.PNG";
import kid from "../assets/kid.PNG";
import teen from "../assets/teen.PNG";
import "../../../css/RawData.css";


class RawData extends Component {
  render() {
    return (
        <div className="rawContent">
        <div className="rawMain">
          <div className="rawImages">
              <img src={child}></img>
              <p>الاول ابتدائي​</p>
              <img src={kid}></img>
              <p>الاول المتوسط​</p>
              <img src={teen}></img>
              <p>الاعدادية​</p>
          </div>
          <div>
              <div className="rawHead">البيانات الاولية ​</div>
              <div className="rawDetails">
                <div className="rawIcon">بغداد​</div>
                <div>المدينة او القرية:​</div>
                <div className="rawIcon">بغداد​</div>
                <div>المحافظة:​</div>
                <div className="rawIcon">ذكر​</div>
                <div>الجنس:​</div>
                <div className="rawIcon">علي محمد احمد​</div>
                <div>اسم التلميذ واللقب:​</div>
                <div className="rawIcon">الاوسط​</div>
                <div>ترتيب التلميذ بين اخوانه:​</div>
                <div className="rawIcon">2017594618347​</div>
                <div>رقم الجنسية العراقية :​</div>
                <div className="rawIcon">07712345678​</div>
                <div>رقم الهاتف:​</div>
                <div className="rawIcon">بغداد/المنصور​</div>
                <div>عنوان المسكن:​</div>
                <div className="rawIcon">محمد احمد عليِ​</div>
                <div>الاسم الثلاثي لولي الامر:​</div>
                <div className="rawIcon">العراق/10/3/2017​</div>
                <div>محل وتاريخ التولد:​</div>
                <div className="rawIcon">محامي​</div>
                <div>مهنة ولي الامر:​</div>
                <div className="rawIcon">اب​</div>
                <div>صلة ولي الامر بالتلميذ:​</div>
                <div className="rawIcon">نعم​</div>
                <div>هل الام على قيد الحياة:​</div>
                <div className="rawIcon">نعم​</div>
                <div>هل الاب على قيد الحياة:​</div>
                <div className="rawIcon">بكلوريوس​</div>
                <div>التحصيل الدراسي للأم:​</div>
                <div className="rawIcon">بكلوريوس​</div>
                <div>التحصيل الدراسي للأب:​</div>
              </div>
              <div className="rawFinish">
                  <div className="rawIcon">لايوجد</div>
                  <div>التغيرات التي تطرأ على البيانات السابقة:​</div>
              </div>
              <div className="rawloginButton">
                <NavLink className="rawloginButtonTag" to="/history">التالي​</NavLink>
            </div>
          </div>
        </div>
      </div>
    );
  }
}

export default RawData;
