$(document).on('input', '.firstname', function() {
    var name = $(this).val();
    var error_class = $(this).attr('name') + '_err';

    if (!/^[a-zA-Z]*$/.test(name)) {
        $('.' + error_class).show().text('Only letters are allowed.');
    } else {
        $('.' + error_class).hide().text('');
    }

    var sanitizedName = name.replace(/[^a-zA-Z]/g, '');

    if (sanitizedName.length > 0) {
        sanitizedName = sanitizedName.charAt(0).toUpperCase() + sanitizedName.slice(1).toLowerCase();
    }

    $(this).val(sanitizedName);
});

$(document).on('input', '.name', function() {
    var name = $(this).val();
    var error_class = $(this).attr('name') + '_err';

    if (!/^[a-zA-Z ]*$/.test(name)) {
        $('.' + error_class).show().text('Only letters and spaces are allowed.');
    } else {
        $('.' + error_class).hide().text('');
    }

    var sanitizedName = name.replace(/[^a-zA-Z ]/g, '');

    sanitizedName = sanitizedName.replace(/^\s+/, '');

    sanitizedName = sanitizedName.replace(/\s{2,}/g, ' ');

    sanitizedName = sanitizedName.replace(/\b\w/g, function(match) {
        return match.toUpperCase();
    });

    $(this).val(sanitizedName);
});

$(document).on('input', '.username', function() {
    var username = $(this).val();
    var error_class = $(this).attr('name') + '_err';
    
    if (!/^[a-zA-Z0-9_]*$/.test(username)) {
        $('.' + error_class).show().text('Only numbers, letters, and underscore are allowed.');
    }else {
        $('.' + error_class).hide().text('');
    }
    
    var sanitizedUsername = username.replace(/[^a-zA-Z0-9_]/g, ''); 

    sanitizedUsername = sanitizedUsername.toLowerCase(); 
    $(this).val(sanitizedUsername); 
});

$(document).on('input', '.email', function() {
    var email = $(this).val().toLowerCase(); 
    var errorClass = $(this).attr('name') + '_err';

    var emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

    if (!emailRegex.test(email)) {
        $('.' + errorClass).show().text('Enter a valid email address.');
    } else {
        $('.' + errorClass).hide().text('');
    }
    

    $(this).val(email); // Update input with lowercase value
});

$(document).on('input', '.mobile', function() {
    var mobile = $(this).val();
    var error_class = $(this).attr('name') + '_err';

    // Remove non-numeric characters
    var sanitizedMobile = mobile.replace(/[^0-9]/g, '');

    // Check if first digit is greater than 5
    if (sanitizedMobile.length > 0 && sanitizedMobile.charAt(0) <= '5') {
        $('.' + error_class).show().text('Invalid Mobile Number.');
    } else {
        $('.' + error_class).hide().text('');
    }

    $(this).val(sanitizedMobile);
});