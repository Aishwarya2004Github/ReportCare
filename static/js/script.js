// Sidebar Toggle
function toggleMenu() {
    const menu = document.getElementById("sideMenu");
    menu.style.left = (menu.style.left === "0px") ? "-280px" : "0px";
}

// Role Change Logic
function handleRoleChange() {
    const role = document.getElementById('roleSelector').value;
    const labLicense = document.getElementById('labLicense');
    const nameInput = document.getElementById('nameInput');
    const sigLabel = document.getElementById('sigLabel');

    if (role === 'Lab') {
        labLicense.style.display = 'block';
        labLicense.required = true;
        nameInput.placeholder = "Laboratory Name *";
        sigLabel.innerText = "Official Lab Stamp Upload *";
    } else {
        labLicense.style.display = 'none';
        labLicense.required = false;
        nameInput.placeholder = "Full Name *";
        sigLabel.innerText = "Digital Signature Upload *";
    }
}

// Image Preview
function previewProfile(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('previewImg').src = e.target.result;
        }
        reader.readAsDataURL(input.files[0]);
    }
}


/* STICKY NAVBAR SHADOW ON SCROLL */
window.addEventListener("scroll", () => {
    const navbar = document.querySelector(".navbar");
    if (window.scrollY > 10) {
        navbar.classList.add("scrolled");
    } else {
        navbar.classList.remove("scrolled");
    }
});

let slideIndex = 0;

function showSlides() {
    let i;
    let slides = document.getElementsByClassName("slide");
    
    // Sabhi 6 slides ko chhupao
    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";  
    }
    
    slideIndex++;
    
    // Agar 6 slide khatam ho jayein to wapis 1st par jao
    if (slideIndex > slides.length) {
        slideIndex = 1;
    }    
    
    // Sirf current slide ko Flex dikhao (taaki professional layout bana rahe)
    slides[slideIndex-1].style.display = "flex";  
    
    // Har 4 second mein slide badlo
    setTimeout(showSlides, 4000); 
}

// Page load hote hi function start karein
document.addEventListener("DOMContentLoaded", showSlides);


// Optional: Form Validation check before submit
document.addEventListener('DOMContentLoaded', () => {
    const regForm = document.getElementById('regForm');
    if (regForm) {
        regForm.addEventListener('submit', function(e) {
            const pass = document.getElementsByName('password')[0].value;
            const confirmPass = document.getElementsByName('confirm_password')[0].value;

            if (pass !== confirmPass) {
                e.preventDefault();
                alert("Passwords do not match!");
            }
        });
    }
});

// --- PROFILE PAGE FUNCTIONS ---

/**
 * Live preview of profile photo before uploading
 */

/**
 * Confirm before deleting the account
 */
function toggleDeleteModal() {
    const modal = document.getElementById('deleteModal');
    if (modal) {
        modal.style.display = (modal.style.display === 'none' || modal.style.display === '') ? 'flex' : 'none';
    }
}

// Gender logic to hide pregnancies
function handlePregnancyVisibility(gender) {
    const pregGroup = document.getElementById('preg-group');
    const pregInput = document.getElementById('pregnancies');
    
    if (gender === 'Male') {
        pregGroup.style.display = 'none';
        pregInput.value = 0; // Male ke liye automatic 0
    } else {
        pregGroup.style.display = 'flex';
    }
}

// 1. Manual Gender Change Listener
document.getElementById('m_gender').addEventListener('change', function() {
    handlePregnancyVisibility(this.value);
});

// 2. Existing Patient Selection Listener
document.getElementById('patient_id').addEventListener('change', async function() {
    const pId = this.value;
    if (!pId) return;

    // Backend se patient ka gender mangwana (Make sure you have this route)
    const resp = await fetch(`/api/get-patient-gender/${pId}`);
    const data = await resp.json();
    
    if (data.gender) {
        handlePregnancyVisibility(data.gender);
        // Age auto-fill bhi kar dete hain
        if(data.age) document.getElementById('age').value = data.age;
    }
});

document.getElementById('regForm').onsubmit = function(e) {
    const role = document.getElementById('roleSelector').value;
    const license = document.getElementById('labLicense').value.toUpperCase();

    if (role === 'Lab') {
        if (!license.startsWith('LAB-')) {
            e.preventDefault(); // Form submit hone se rok dega
            showToast("License Number must start with 'LAB-' (e.g., LAB-12345)", "#e74c3c");
            return false;
        }
    }
};