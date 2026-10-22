const identitySelect = document.querySelector("#identity");
const recordForm = document.querySelector("#record-form");
const recordSelect = document.querySelector("#record-id");
const summaryButton = document.querySelector("#summary-button");
const responseStatus = document.querySelector("#response-status");
const responseMessage = document.querySelector("#response-message");
const responseBody = document.querySelector("#response-body");

const TOKENS = {
  member_a: "token-member-a",
  admin_a: "token-admin-a",
  member_b: "token-member-b",
  admin_b: "token-admin-b",
};

function showResponse(status, body, message) {
  responseStatus.textContent = `HTTP ${status}`;
  responseStatus.className = "status";

  if (status >= 200 && status < 300) {
    responseStatus.classList.add("success");
  } else if (status === 401 || status === 403 || status === 404) {
    responseStatus.classList.add("denied");
  } else {
    responseStatus.classList.add("error");
  }

  responseMessage.textContent = message;
  responseBody.replaceChildren(
    Object.assign(document.createElement("code"), {
      textContent: JSON.stringify(body, null, 2),
    }),
  );
}

async function sendRequest(path) {
  const token = TOKENS[identitySelect.value];

  responseStatus.textContent = "Request in progress…";
  responseStatus.className = "status";
  responseMessage.textContent = "Waiting for the API response.";
  responseBody.replaceChildren(
    Object.assign(document.createElement("code"), {
      textContent: "Sending request…",
    }),
  );

  recordForm.querySelector("button").disabled = true;
  summaryButton.disabled = true;

  try {
    const response = await fetch(path, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const rawBody = await response.text();
    let body;

    try {
      body = rawBody ? JSON.parse(rawBody) : null;
    } catch {
      body = { raw_response: rawBody };
    }

    const message =
      response.status === 200
        ? "The API returned a successful response."
        : response.status === 401
          ? "Authentication failed: the API did not accept the credentials."
          : response.status === 403
            ? "The API refused this function because permission was insufficient."
            : response.status === 404
              ? "The API did not return an accessible record or resource."
              : `The API responded with HTTP ${response.status}.`;

    showResponse(response.status, body, message);
  } catch (error) {
    responseStatus.textContent = "Request failed";
    responseStatus.className = "status error";
    responseMessage.textContent =
      "The API could not be reached. Confirm the local server is running.";
    responseBody.replaceChildren(
      Object.assign(document.createElement("code"), {
        textContent: String(error),
      }),
    );
  } finally {
    recordForm.querySelector("button").disabled = false;
    summaryButton.disabled = false;
  }
}

recordForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const recordId = recordSelect.value;
  sendRequest(`/records/${encodeURIComponent(recordId)}`);
});

summaryButton.addEventListener("click", () => {
  sendRequest("/admin/summary");
});
