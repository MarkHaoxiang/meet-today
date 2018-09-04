
// Front end

//Scrolling navbar
console.log("meet-today.js loaded")
var myNav = document.getElementById("mynav");
window.onscroll = function () {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop || document.body.scrollTop || 0;
    if (myNav == null){
        console.log("check")
        myNav = document.getElementById("mynav");
    }
    if (scrollTop >= 100 ) {

            myNav.classList.add("nav-colored");
            myNav.classList.remove("nav-transparent");
            myNav.classList.add("navbar-light");
            myNav.classList.add("border-bottom");
            myNav.classList.remove("navbar-dark");
        }
        else {
            myNav.classList.add("nav-transparent");
            myNav.classList.remove("nav-colored");
            myNav.classList.remove("navbar-light");
            myNav.classList.add("navbar-dark")
            myNav.classList.remove("border-bottom");
        }
    };
