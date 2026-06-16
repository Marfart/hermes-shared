import fs from "node:fs/promises";
import path from "node:path";

const INPUT_PATH =
  process.argv[2] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development/whatsapp_priority_queue_2026-06-01.json";
const OUTPUT_DIR =
  process.argv[3] ||
  "C:/Users/Admin/AppData/Local/hermes/memories/buyer-development";
const OUTPUT_BASENAME =
  process.argv[4] ||
  "whatsapp_messages_2026-06-01";
const WEBSITE_URL = "https://bliiot.com/";

const SHARED_VARIANTS = {
  greeting: [
    "Hope you are having a wonderful day.",
    "Hope you are having a great day.",
    "Wishing you a pleasant day.",
    "Hope your day is going well.",
    "Hope you are enjoying a good day.",
  ],
  intro: [
    "Hi, this is Kali from BLIIOT.",
    "Hello, this is Kali from BLIIOT.",
    "Hi, Kali here from BLIIOT.",
    "Hello, Kali from BLIIOT here.",
    "Hi, I am Kali from BLIIOT.",
  ],
  link: [
    `You can have a quick look here: ${WEBSITE_URL}`,
    `Our website is here: ${WEBSITE_URL}`,
    `You may also check our website here: ${WEBSITE_URL}`,
    `If helpful, here is our website: ${WEBSITE_URL}`,
    `For a quick overview, here is our website: ${WEBSITE_URL}`,
  ],
  close: [
    "If you are interested, I can send a short catalog.",
    "If useful, I can send a short catalog.",
    "Let me know if you would like a short catalog.",
    "I can also send a short catalog for reference.",
    "If that sounds useful, I can send a short catalog.",
  ],
};

const STYLE_BANKS = {
  scada_plc: {
    company_pitch: [
      "BLIIOT is a supplier of industrial IoT hardware, focusing on industrial gateways, edge controllers, and remote data acquisition devices for automation projects.",
      "BLIIOT mainly provides industrial gateways, ARM edge controllers, and remote I/O products for PLC, SCADA, and industrial communication applications.",
      "Our company focuses on industrial IoT connectivity products, especially gateways, edge controllers, and field data acquisition devices used in automation systems.",
      "BLIIOT is a manufacturer of industrial communication and IIoT hardware, with product lines for gateways, edge controllers, and remote monitoring devices.",
    ],
    observation: [
      (lead) => `I noticed that your company is active in ${shortNeedText(lead)}.`,
      (lead) => `From your profile, your team seems focused on ${shortNeedText(lead)}.`,
      (lead) => `Your business looks closely connected with ${shortNeedText(lead)}.`,
      (lead) => `It looks like your projects involve ${shortNeedText(lead)}.`,
    ],
    offer: [
      (lead) =>
        `For this type of work, we usually recommend ${shortProductText(lead)} for PLC/SCADA connectivity, protocol conversion, and remote monitoring.`,
      (lead) =>
        `Our ${shortProductText(lead)} are often used in PLC, SCADA, and industrial communication projects.`,
      (lead) =>
        `We have ${shortProductText(lead)} that fit applications involving PLC data collection and SCADA integration.`,
      (lead) =>
        `Our relevant product line includes ${shortProductText(lead)} for industrial communication, field data access, and SCADA-side integration.`,
    ],
    value: [
      "They can help shorten integration time and improve remote visibility in industrial projects.",
      "They are widely used where stable industrial communication and quick deployment matter.",
      "They are suitable for projects that need protocol conversion, remote access, and reliable field data collection.",
      "They are often selected by integrators who need practical industrial networking and monitoring hardware.",
    ],
    cta: [
      "If you have a PLC or SCADA project, I can suggest suitable models and pricing.",
      "If you are evaluating an industrial communication project, I can recommend suitable models.",
      "If you have a current requirement, I can suggest matching models.",
      "If this is relevant to your work, I can send a few suitable options.",
    ],
  },
  system_integrator: {
    company_pitch: [
      "BLIIOT is an industrial IoT hardware company focused on gateways, edge controllers, cellular routers, and remote I/O for system integration projects.",
      "Our company mainly develops industrial gateways, ARM-based edge controllers, and remote data acquisition products for automation and integration applications.",
      "BLIIOT focuses on industrial connectivity and edge hardware, especially for integrators working on device networking, protocol conversion, and remote monitoring.",
      "We are a supplier of industrial IoT hardware, with product lines covering gateways, edge controllers, routers, and remote I/O modules.",
    ],
    observation: [
      (lead) => `I saw that your team is working in ${shortNeedText(lead)}.`,
      (lead) => `Your company seems active in integration-oriented work such as ${shortNeedText(lead)}.`,
      (lead) => `From your profile, it looks like your business is closely related to ${shortNeedText(lead)}.`,
      (lead) => `Your solutions appear highly relevant to ${shortNeedText(lead)}.`,
    ],
    offer: [
      (lead) =>
        `For this kind of integration work, we can offer ${shortProductText(lead)} for industrial connectivity, edge data collection, and remote monitoring.`,
      (lead) =>
        `Our product line includes ${shortProductText(lead)}, which are suitable for integration projects involving field devices and cloud platforms.`,
      (lead) =>
        `We supply ${shortProductText(lead)} for projects involving protocol conversion, device networking, and remote field access.`,
      (lead) =>
        `${shortProductText(lead)} are suitable for integrators working on automation, monitoring, and device communication projects.`,
    ],
    value: [
      "They are suitable for system integrators, OEM projects, and end-user monitoring applications.",
      "They can help integrators reduce development time and build reliable industrial solutions faster.",
      "They are often chosen for projects that need industrial communication hardware with practical deployment flexibility.",
      "They work well for multi-site monitoring, data acquisition, and edge-side integration tasks.",
    ],
    cta: [
      "If you have current or upcoming integration projects, I can suggest suitable models.",
      "If your team is evaluating new automation projects, I can recommend suitable products.",
      "If this fits your current pipeline, I can share a few matching models.",
      "If useful, I can send product suggestions for integrator-type applications.",
    ],
  },
  energy_monitoring: {
    company_pitch: [
      "BLIIOT is focused on industrial IoT hardware for remote monitoring, industrial communication, and field data acquisition.",
      "Our company mainly provides industrial gateways, cellular routers, RTU-type products, and edge controllers for monitoring and utility projects.",
      "BLIIOT develops industrial connectivity hardware used in remote monitoring, utility data transmission, and distributed equipment access.",
      "We are an industrial IoT hardware supplier with products for gateways, routers, and remote acquisition in monitoring and utility scenarios.",
    ],
    observation: [
      (lead) => `I noticed that your company is active in ${shortNeedText(lead)}.`,
      (lead) => `It seems your projects are related to ${shortNeedText(lead)}.`,
      (lead) => `From your profile, your solutions look relevant to ${shortNeedText(lead)}.`,
      (lead) => `Your business appears to align well with ${shortNeedText(lead)}.`,
    ],
    offer: [
      (lead) =>
        `For these applications, we usually recommend ${shortProductText(lead)} for energy monitoring, remote utility access, and industrial data transmission.`,
      (lead) =>
        `Our ${shortProductText(lead)} are often used in power, utility, and monitoring projects that need reliable field connectivity.`,
      (lead) =>
        `We offer ${shortProductText(lead)} for remote monitoring, device networking, and utility-side data collection.`,
      (lead) =>
        `Our product range includes ${shortProductText(lead)} for projects involving remote monitoring, energy management, and industrial communication.`,
    ],
    value: [
      "They are widely used in smart monitoring, utility, and energy-related scenarios.",
      "They can help improve remote visibility and reduce integration effort in monitoring projects.",
      "They are often selected for projects that need reliable data access from field equipment and remote sites.",
      "They are designed for practical deployment in utility monitoring, industrial telemetry, and remote access scenarios.",
    ],
    cta: [
      "If you have monitoring or energy-related projects, I can suggest suitable models.",
      "If you are evaluating a remote monitoring project, I can recommend suitable products.",
      "If relevant, I can send a few matching products for these applications.",
      "If this fits your current needs, I can suggest suitable devices.",
    ],
  },
  generic_iiot: {
    company_pitch: [
      "BLIIOT is an industrial IoT hardware company focused on gateways, routers, edge controllers, and remote I/O products.",
      "Our company mainly provides industrial communication and IIoT hardware for device connectivity, data acquisition, and remote monitoring.",
      "BLIIOT develops industrial IoT products such as gateways, edge controllers, and remote data acquisition devices for automation and monitoring projects.",
      "We are a supplier of industrial IoT connectivity hardware, especially for protocol conversion, edge access, and industrial networking.",
    ],
    observation: [
      (lead) => `Your business seems highly relevant to ${shortNeedText(lead)}.`,
      (lead) => `I noticed that your company is active in ${shortNeedText(lead)}.`,
      (lead) => `From your company profile, it looks like your team is involved in ${shortNeedText(lead)}.`,
      (lead) => `Your solutions appear to be closely connected with ${shortNeedText(lead)}.`,
    ],
    offer: [
      (lead) =>
        `For this kind of demand, our ${shortProductText(lead)} are often used for field data acquisition, protocol conversion, and IIoT integration.`,
      (lead) =>
        `We offer ${shortProductText(lead)} for remote monitoring, industrial communication, and edge-side data collection.`,
      (lead) =>
        `We provide ${shortProductText(lead)} that can help with device connectivity, protocol conversion, and IIoT projects.`,
      (lead) =>
        `Our product line includes ${shortProductText(lead)}, which are suitable for industrial communication, edge control, and monitoring projects.`,
    ],
    value: [
      "They are widely used in automation, IIoT, and smart monitoring scenarios.",
      "They are often chosen for projects that need reliable industrial communication and fast deployment.",
      "They can help improve data visibility while keeping deployment practical for industrial sites.",
      "They are designed for practical use in industrial automation, smart factory, and edge integration scenarios.",
    ],
    cta: [
      "If you are working on IIoT projects, I can share suitable product options.",
      "If you have current or upcoming projects, I can suggest suitable models.",
      "If you are evaluating new IIoT or automation projects, I can recommend suitable products.",
      "If this is relevant to your work, I can send a few suitable options.",
    ],
  },
};

function shortNeedText(lead) {
  const needs = [lead.inferred_need_1, lead.inferred_need_2].filter(Boolean);
  if (!needs.length) return "IIoT and industrial automation integration";
  return needs.slice(0, 2).join(" / ");
}

function shortProductText(lead) {
  const rawProducts = [lead.recommended_product_1, lead.recommended_product_2].filter(Boolean);
  if (!rawProducts.length) return "industrial gateways and edge devices";
  const normalized = rawProducts.map((product) => {
    const text = String(product);
    if (/gateways?\/routers?/i.test(text)) return "industrial gateways and routers";
    if (/armxy|edge computers?|edge controllers?/i.test(text)) return "ARM edge controllers";
    if (/remote io|rtu|data acquisition/i.test(text)) return "remote I/O and data acquisition devices";
    return text.replace(/^BLIIOT\s+/i, "").replace(/\s*\([^)]*\)/g, "").trim();
  });
  const unique = [...new Set(normalized)].slice(0, 2);
  if (unique.length === 1) return unique[0];
  return `${unique[0]} together with ${unique[1]}`;
}

function classifyStyle(lead) {
  const needText = [lead.inferred_need_1, lead.inferred_need_2]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
  const fullText = [
    lead.inferred_need_1,
    lead.inferred_need_2,
    lead.source_description,
    lead.domain,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  if (/plc|scada|dcs|protocol/.test(needText)) return "scada_plc";
  if (/energy|utility|bems|power/.test(needText)) return "energy_monitoring";
  if (/integrator|integration|system|automation gateway|edge integration/.test(fullText)) return "system_integrator";
  return "generic_iiot";
}

function pickIndex(length, seed, multiplier, offset) {
  return (seed * multiplier + offset) % length;
}

function buildMessagePayload(lead) {
  const seed = Number(lead.queue_id || 0);
  const styleId = classifyStyle(lead);
  const style = STYLE_BANKS[styleId];

  const introIndex = pickIndex(SHARED_VARIANTS.intro.length, seed, 1, 0);
  const observationIndex = pickIndex(style.observation.length, seed, 2, 1);
  const offerIndex = pickIndex(style.offer.length, seed, 3, 2);
  const valueIndex = pickIndex(style.value.length, seed, 5, 1);
  const ctaIndex = pickIndex(style.cta.length, seed, 7, 3);
  const linkIndex = pickIndex(SHARED_VARIANTS.link.length, seed, 11, 2);
  const closeIndex = pickIndex(SHARED_VARIANTS.close.length, seed, 13, 4);

  const parts = [
    `${SHARED_VARIANTS.greeting[pickIndex(SHARED_VARIANTS.greeting.length, seed, 19, 6)]}\n\n${SHARED_VARIANTS.intro[introIndex]} ${style.company_pitch[pickIndex(style.company_pitch.length, seed, 17, 5)]}`,
    `${style.observation[observationIndex](lead)} ${style.offer[offerIndex](lead)}`,
    `${style.cta[ctaIndex]} ${SHARED_VARIANTS.link[linkIndex]}`,
    SHARED_VARIANTS.close[closeIndex],
  ];

  return {
    style_id: styleId,
    variant_id: `${styleId}-v${introIndex}-${observationIndex}-${offerIndex}-${valueIndex}-${ctaIndex}-${linkIndex}-${closeIndex}`,
    variant_parts: {
      intro: introIndex,
      observation: observationIndex,
      offer: offerIndex,
      value: valueIndex,
      cta: ctaIndex,
      link: linkIndex,
      close: closeIndex,
    },
    message: parts.join("\n\n"),
  };
}

const queue = JSON.parse(await fs.readFile(INPUT_PATH, "utf8"));
const messages = queue.map((lead) => {
  const payload = buildMessagePayload(lead);
  return {
    ...lead,
    style_id: payload.style_id,
    variant_id: payload.variant_id,
    variant_parts: payload.variant_parts,
    message: payload.message,
  };
});

await fs.mkdir(OUTPUT_DIR, { recursive: true });
const outPath = path.join(OUTPUT_DIR, `${OUTPUT_BASENAME}.json`);
await fs.writeFile(outPath, JSON.stringify(messages, null, 2), "utf8");

console.log(
  JSON.stringify(
    {
      count: messages.length,
      outPath,
      sample: messages[0] || null,
    },
    null,
    2
  )
);
