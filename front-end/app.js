"use strict";
const PHOTO_API_KEY = "__PHOTO_API_KEY_AT_BUILD__";
const el = id => document.getElementById(id);
function client() {
  const key = PHOTO_API_KEY;
  if (!key || key.startsWith("__PHOTO_API_KEY_")) throw new Error("Photo album configuration is missing. Please contact the site owner.");
  return apigClientFactory.newClient({apiKey: key});
}
function errorMessage(error) {
  const response = error && error.response;
  const message = response && response.data && response.data.message;
  return message || (error && error.message) || "Request failed. Please try again shortly.";
}
function imageUrl(result) {
  const value = typeof result === "string" ? result : result.url || result.presignedUrl || result.presigned_url || result.imageUrl;
  if (!value) return null;
  try { const url = new URL(value); return url.protocol === "https:" ? url.href : null; } catch (_) { return null; }
}
el("search-form").addEventListener("submit", async event => {
  event.preventDefault();
  const status = el("search-status");
  el("search-button").disabled = true;
  el("results").replaceChildren();
  status.textContent = "Searching…";
  try {
    const response = await client().searchGet({q: el("query").value.trim()}, null, {});
    const data = typeof response.data === "string" ? JSON.parse(response.data) : response.data;
    const results = Array.isArray(data) ? data : data.results;
    if (!Array.isArray(results)) throw new Error("Unexpected search response format.");
    let displayed = 0;
    for (const result of results) {
      const url = imageUrl(result);
      if (!url) continue;
      const figure = document.createElement("figure");
      const img = document.createElement("img");
      const caption = document.createElement("figcaption");
      const name = result.objectKey || "Matching photo";
      img.alt = name; img.src = url; img.loading = "lazy";
      img.addEventListener("error", () => { caption.textContent = name + " — image unavailable; search again for a fresh link."; });
      caption.textContent = name;
      figure.append(img, caption); el("results").append(figure); displayed++;
    }
    if (results.length && !displayed) throw new Error("Results arrived without a recognized image URL field. Check the search response.");
    status.textContent = displayed ? displayed + (displayed === 1 ? " photo found." : " photos found.") : "No photos found. Try another label.";
  } catch (error) { status.textContent = errorMessage(error); }
  finally { el("search-button").disabled = false; }
});
el("upload-form").addEventListener("submit", async event => {
  event.preventDefault();
  const status = el("upload-status");
  el("upload-button").disabled = true;
  status.textContent = "Uploading…";
  try {
    const api = client();
    const file = el("photo").files[0];
    if (!file || !["image/jpeg", "image/png"].includes(file.type)) throw new Error("Choose a JPEG or PNG image.");
    if (!file.size || file.size > 7 * 1024 * 1024) throw new Error("Choose a nonempty image up to 7 MB.");
    const labels = el("labels").value.split(",").map(value => value.trim()).filter(Boolean).join(",");
    if (/[^\x20-\x7E]/.test(labels)) throw new Error("Use plain English letters, numbers, and punctuation for custom labels.");
    const filename = Date.now() + "-" + file.name.replace(/[^a-zA-Z0-9._-]/g, "_");
    await api.photosPut({filename, "Content-Type": file.type, "x-amz-meta-customLabels": labels}, file, {});
    status.textContent = "Uploaded " + filename + ". Automatic labeling may take a few seconds. Then search for a custom label or an object in the image.";
    el("upload-form").reset();
  } catch (error) { status.textContent = errorMessage(error); }
  finally { el("upload-button").disabled = false; }
});
