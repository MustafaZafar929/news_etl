from sentence_transformers import SentenceTransformer
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
import hdbscan
import matplotlib.pyplot as plt

# -------------------------
# 1. Generate embeddings
# -------------------------
sentences = [
"â€¢ Fox-Dominion trial delay 'is not unusual,' judge says â€¢ Fox News' defamation battle isn't stopping Trump's election lies",
"The judge just announced in court that a settlement has been reached in the historic defamation case between Fox News and Dominion Voting Systems.",
"A settlement has been reached in Dominion Voting Systems' defamation case against Fox News, the judge for the case announced.",
"The network will pay more than $787 million to Dominion, a lawyer for the company said.",
"â€¢ DeSantis goes to Washington, a place he once despised, looking for support to take on Trump â€¢ Opinion: For the GOP to win, it must ditch Trump â€¢ Chris Christie mulling 2024 White House bid â€¢ Analysis: The fire next time has begun burning in Tennessee",
"â€¢ 'A major part of Ralph died': Aunt of teen shot after ringing wrong doorbell speaks â€¢ 20-year-old woman shot after friend turned into the wrong driveway in upstate New York, officials say",
"Newly released body camera footage shows firefighters and sheriff's deputies rushing to help actor Jeremy Renner after a near-fatal snowplow accident in January.",
"The 'Avengers' actor broke more than 30 bones and suffered other severe injuries.",
"It's sourdough bread and handstands for Jake Gyllenhaal and Jamie Lee Curtis.",
"A tiny intruder infiltrated White House grounds Tuesday, prompting a swift response from the US Secret Service.",
"Jamie Foxx remains hospitalized in Georgia nearly a week after his daughter revealed the actor experienced a 'medical complication,' a source with knowledge of the matter told CNN on Monday.",
"A 13-year-old in Ohio has died after 'he took a bunch of Benadryl,' trying a dangerous TikTok challenge that's circulating online, according to a CNN affiliate and a GoFundMe account from his family.",
"Pizza guy delivers more than a pie, taking out a fleeing suspect.",
"Netflix is officially winding down the business that helped make it a household name.",
"Artificial intelligence tools such as ChatGPT could lead to a 'turbocharging' of consumer harms including fraud and scams, and the US government has substantial authority to crack down on AI-driven consumer harms under existing law, members of the Federal Trade Commission said Tuesday.",
"Gobbling up too many refined wheat and rice products, along with eating too few whole grains, is fueling the growth of new cases of type 2 diabetes worldwide, according to a new study that models data through 2018.",
"At some middle and high schools in the United States, 1 in 4 teens report they've abused prescription stimulants for attention deficit hyperactivity disorder during the year prior, a new study found.",
"CEO Tim Cook personally welcomed customers to the new Apple store in Mumbai as the tech company opens its first retail stores in India.",
"Senate Democrats railed against Justice Clarence Thomas on Tuesday amid reports that the Supreme Court conservative failed to disclose luxury travel, gifts and a real estate transaction involving a GOP megadonor.",
"In a highly controversial move, some Israeli MPs are trying to introduce the death penalty for Palestinian attackers.",
"Two Russian men who claim to be former Wagner Group commanders have told a human rights activist that they killed children and civilians during their time in Ukraine.",
"CNN panelists react to Florida Gov. Ron DeSantis floating the idea of building a competing theme park next to Disney World in Orlando.",
"House Speaker Kevin McCarthy traveled to Wall Street on Monday to deliver a fresh warning that the House GOP majority will refuse to lift a cap on government borrowing unless Biden agrees to spending cuts that would effectively neutralize his domestic agenda.",
"The US has sensitive nuclear technology at a nuclear power plant inside Ukraine and is warning Russia not to touch it, according to a letter the US Department of Energy sent to Russia's state-owned nuclear energy firm Rosatom last month.",
"Atiq Ahmed, a former lawmaker in India's parliament, convicted of kidnapping, was shot dead along with his brother while police were escorting them for a medical check-up in a slaying caught on live television on Saturday.",
"The U.S. Food and Drug Administration amended the terms of its emergency use authorizations for the Pfizer and Moderna bivalent vaccines on Tuesday, allowing people ages 65 and older and certain people with weakened immunity to get additional doses before this fall's vaccination campaigns.",
"Maine authorities have detained a person of interest and continue to investigate after two shooting incidents that appear to be connected left at least four people dead and three others injured.",
"Buffalo Bills safety Damar Hamlin said Tuesday his cardiac arrest during an NFL game in January was caused by commotio cordis.",
"Polish pilot Lukasz Czepiela made history after landing a plane on a helipad at the top of a 56-story hotel in Dubai.",
"The top US Navy admiral ardently defended a non-binary sailor on Tuesday amid some criticism from Republican lawmakers.",
"The Fulton County District Attorney's office said some fake electors for Donald Trump have implicated each other in potential criminal activity.",
"It's April 18, the official deadline to file your federal and state income tax returns for 2022.",
"A German artist has rejected an award from a prestigious international photography competition after revealing that his submission was generated by Artificial Intelligence.",
"What does intimacy look like for seniors?",
"China's economy is off to a solid start in 2023 following its emergence from three years of strict pandemic restrictions.",
"McDonald's is rolling out a series of changes designed to improve its signature burgers.",
"Shares of Google-parent Alphabet fell more than 3% in early trading Monday after a report sparked concerns that its core search engine could lose market share to AI-powered rivals."
]



model = SentenceTransformer("all-MiniLM-L6-v2")

embeddings = model.encode(
    sentences,
    normalize_embeddings=True  # IMPORTANT for DBSCAN + cosine
)   

# -------------------------
# 2. Run DBSCAN
# -------------------------
dbscan = DBSCAN(
    eps=0.4,          # distance threshold (tune this!)
    min_samples=2,
    metric="cosine"
)

labels = dbscan.fit_predict(embeddings)

print("Cluster labels:")
for s, l in zip(sentences, labels):
    print(f"{l}: {s}")

# -------------------------
# 3. Reduce to 2D for visualization
# -------------------------
pca = PCA(n_components=2)
embeddings_2d = pca.fit_transform(embeddings)

# -------------------------
# 4. Plot
# -------------------------
plt.figure(figsize=(8, 6))

unique_labels = set(labels)

for label in unique_labels:
    idxs = labels == label

    if label == -1:
        # Noise points
        plt.scatter(
            embeddings_2d[idxs, 0],
            embeddings_2d[idxs, 1],
            c="gray",
            marker="x",
            label="Noise"
        )
    else:
        plt.scatter(
            embeddings_2d[idxs, 0],
            embeddings_2d[idxs, 1],
            label=f"Cluster {label}"
        )

# Annotate points
for i, sentence in enumerate(sentences):
    plt.annotate(sentence, (embeddings_2d[i, 0], embeddings_2d[i, 1]), fontsize=8)

plt.title("DBSCAN Clustering of Sentence Embeddings")
plt.legend()
plt.tight_layout()
plt.show()
