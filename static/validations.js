function check()
{
    // Validate email
    var email = document.getElementById('email');
    if (emailValidation(email) == false) {
        return false;
    }

    // Validate username
    var username = document.getElementById("username");
    if (username.value.length < 4)
    {
        alert("Username must be at least 4 characters long");
        username.focus();
        return false;
    }

    // Validate Password
    var password = document.getElementById("password");
    if (password.value.length < 8)
    {
        alert("Password must be at least 8 characters long");
        password.focus();
        return false;
    }

    // Confirm Password
    var confirmation = document.getElementById("confirmation");
    if (password.value != confirmation.value)
    {
        alert("Password must match");
        confirmation.focus();
        return false;
    }
}

//Function for email validation
function emailValidation(inputtext) {
    var emailExp = /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/;
    if (inputtext.value.match(emailExp))
    {
        return true;
    }
    alert("Must provide a valid e-mail");
    inputtext.focus();
    return false;
}

// Function for confirmation
function confirmation(msg)
{
    if (confirm(msg)) {
        return true;
    } else {
        return false;
    }
}

function login_check()
{
    // Validate username & password
    var username = document.getElementById("username");
    var password = document.getElementById("password");
    if (username.value.length < 4 || password.value.length < 8)
    {
        alert("Invalid username and/or password");
        username.focus();
        return false;
    }
}