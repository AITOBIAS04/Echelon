// utils/auth.js

export function logout() {
  // Remove the token from localStorage
  localStorage.removeItem("access_token");
  // Redirect to the login page
  window.location.href = "/login";
}