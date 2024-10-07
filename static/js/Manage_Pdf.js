// app.alert({
//     cMsg: "hello!",
//     cTitle: "onClickEvent",
//     nIcon: 3 
//  });

function removeSetence() {
    app.alert({
        cMsg: "hello!",
        cTitle: "onClickEvent",
        nIcon: 3 
    });
    // access properties using this keyword
    // if ( this.checked ) {
    //     app.alert({
    //         cMsg: "checked!",
    //         cTitle: "onClickEvent",
    //         nIcon: 3 
    //      });
    // } else {
    //     app.alert({
    //         cMsg: "unchecked!",
    //         cTitle: "onClickEvent",
    //         nIcon: 3 
    //      });
    // }
}

this.getField("x").addEventListener("onClick", function () {
    app.alert({
        cMsg: "hello!",
        cTitle: "onClickEvent",
        nIcon: 3 
    });
}, false); 

//var val = prompt("Enter a value");
//this.getField("x").value = "Yes" ;
//this.getField("x").display = display.hidden ;


// if (this.getField("myCheckBox").value != "Off") { 
//     // the box is checked 
// } else { 
// // the box is not checked 
// }