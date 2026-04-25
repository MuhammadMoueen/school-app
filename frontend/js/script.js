const DJANGO_BASE_URL = "http://127.0.0.1:8000";

const FALLBACK_FACILITIES = [
  {
    title: "Classrooms",
    description: "Interactive classrooms that support focused and collaborative learning.",
    image_url: "assets/images/classroom.jpg"
  },
  {
    title: "Labs",
    description: "Science and computer labs for practical experimentation and digital fluency.",
    image_url: "assets/images/elearning.jpg"
  },
  {
    title: "Library",
    description: "A calm academic resource center with curated reading and research support.",
    image_url: "assets/images/campus.jpg"
  },
  {
    title: "Sports",
    description: "Activity and sports spaces that promote teamwork, resilience, and wellbeing.",
    image_url: "assets/images/school-home.jpg"
  },
  {
    title: "Security",
    description: "Comprehensive campus safety practices with controlled access and monitoring.",
    image_url: "assets/images/campus.jpg"
  }
];

function getDjangoBaseUrl() {
  return DJANGO_BASE_URL.replace(/\/$/, "");
}

function isSubPage() {
  return window.location.pathname.includes("/pages/");
}

function toAsset(pathFromRootAssets) {
  return `${isSubPage() ? "../" : ""}${pathFromRootAssets}`;
}

function resolveImageUrl(imageUrl) {
  if (!imageUrl) {
    return toAsset("assets/images/campus.jpg");
  }

  if (imageUrl.startsWith("http://") || imageUrl.startsWith("https://")) {
    return imageUrl;
  }

  if (imageUrl.startsWith("/")) {
    return `${getDjangoBaseUrl()}${imageUrl}`;
  }

  if (imageUrl.startsWith("../assets/") && !isSubPage()) {
    return imageUrl.replace("../", "");
  }

  if (imageUrl.startsWith("assets/")) {
    return toAsset(imageUrl);
  }

  return imageUrl;
}

function showNotice(container, type, message) {
  container.className = `notice ${type}`;
  container.textContent = message;
  container.classList.remove("d-none");
}

function setActiveNav() {
  const currentPage = document.body.dataset.page;
  document.querySelectorAll("[data-nav]").forEach((link) => {
    if (link.dataset.nav === currentPage) {
      link.classList.add("active");
    }
  });
}

async function initSessionLink() {
  const authLink = document.querySelector("[data-auth-link]");
  const profileImg = document.querySelector("[data-profile-image]");
  if (!authLink) {
    return;
  }

  authLink.href = `${getDjangoBaseUrl()}/login/`;

  try {
    const response = await fetch(`${getDjangoBaseUrl()}/api/session/`, {
      method: "GET",
      credentials: "include"
    });

    if (!response.ok) {
      return;
    }

    const session = await response.json();
    authLink.href = session.is_authenticated ? session.dashboard_url : session.login_url;

    if (session.is_authenticated && session.profile_image_url && profileImg) {
      profileImg.src = session.profile_image_url;
      profileImg.classList.remove("d-none");
      authLink.querySelector("[data-default-icon]")?.classList.add("d-none");
    }
  } catch (error) {
    console.warn("Session API unavailable:", error);
  }
}

function buildFacilityCard(item) {
  return `
    <article class="glass card-lift overflow-hidden h-100">
      <img src="${item.image_url}" alt="${item.title}" class="facility-image" loading="lazy">
      <div class="p-4">
        <h3 class="h5 fw-semibold">${item.title}</h3>
        <p class="mb-0 text-secondary">${item.description}</p>
      </div>
    </article>
  `;
}

async function initServicesGrid() {
  const grid = document.getElementById("services-grid");
  if (!grid) {
    return;
  }

  let facilities = [];

  try {
    const response = await fetch(`${getDjangoBaseUrl()}/api/facilities/`, {
      method: "GET"
    });

    if (response.ok) {
      const data = await response.json();
      facilities = Array.isArray(data.facilities) ? data.facilities : [];
    }
  } catch (error) {
    console.warn("Facilities API unavailable:", error);
  }

  const cards = facilities.length > 0 ? facilities : FALLBACK_FACILITIES;

  grid.innerHTML = cards
    .map((item) => {
      const card = {
        ...item,
        image_url: resolveImageUrl(item.image_url)
      };
      return `<div class="col-md-6 col-xl-4">${buildFacilityCard(card)}</div>`;
    })
    .join("");
}

function initContactForm() {
  const form = document.getElementById("contact-form");
  const feedback = document.getElementById("contact-feedback");
  if (!form || !feedback) {
    return;
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const submitButton = form.querySelector("button[type='submit']");
    const formData = new FormData(form);
    const payload = {
      name: formData.get("name")?.toString().trim(),
      email: formData.get("email")?.toString().trim(),
      message: formData.get("message")?.toString().trim()
    };

    submitButton.disabled = true;
    submitButton.textContent = "Sending...";

    try {
      const response = await fetch(`${getDjangoBaseUrl()}/api/contact/`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json().catch(() => ({
        success: false,
        error: "Unable to submit your message right now."
      }));

      if (!response.ok || !data.success) {
        showNotice(feedback, "error", data.error || "Unable to send your message right now.");
        return;
      }

      showNotice(feedback, "success", data.message || "Message sent successfully.");
      form.reset();
    } catch (error) {
      showNotice(feedback, "error", "Server unavailable. Please try again later.");
    } finally {
      submitButton.disabled = false;
      submitButton.textContent = "Send Message";
    }
  });
}

function initYear() {
  document.querySelectorAll("[data-year]").forEach((node) => {
    node.textContent = new Date().getFullYear().toString();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  setActiveNav();
  initSessionLink();
  initServicesGrid();
  initContactForm();
  initYear();
});
