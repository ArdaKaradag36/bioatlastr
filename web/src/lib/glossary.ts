// Plain-Turkish glossary used by /sozluk and by the <Term> tooltips.
// Every explanation describes how THIS project uses the word; nuances we are not sure about are kept general.

export type GlossaryGroup = "DNA ve barkod" | "Barkod bölgeleri" | "Diziler ve veri kaynakları" | "Mesafe ve ağaç" | "Bitki sınıflandırması" | "Sonuçları okumak";

export interface GlossaryEntry {
  id: string; // used in /sozluk#id
  term: string; // as shown
  aka?: string; // other spellings, searched too
  short: string; // one sentence, shown in the tooltip
  more?: string; // longer explanation
  analogy?: string; // everyday comparison
  group: GlossaryGroup;
}

export const GLOSSARY: GlossaryEntry[] = [
  // ---- DNA ve barkod
  {
    id: "dna-barkodu", term: "DNA barkodu", group: "DNA ve barkod",
    short: "Bir türü tanımak için kullanılan, DNA'nın kısa ve herkesçe aynı seçilen bir bölümünün harf dizisi.",
    more: "Bilim insanları birçok türde aynı kısa DNA bölümüne bakar ve harf dizilerini karşılaştırır. Bu sitenin sorusu şudur: böyle kısa bir bölüm, Türkiye'deki bitki türlerini birbirinden ayırmaya yeter mi?",
    analogy: "Marketteki ürün barkodu gibi düşünebilirsiniz; ama burada her tür için tek ve kesin bir kod olduğu varsayılmaz, ne kadar işe yaradığı ölçülür.",
  },
  {
    id: "dizi", term: "Dizi (sekans)", aka: "sekans", group: "DNA ve barkod",
    short: "Bir DNA parçasındaki harflerin (A, C, G, T) art arda yazılmış hali.",
    more: "Bu sitede bir \"dizi\", bir bitki örneğinden okunmuş ve herkese açık arşive yüklenmiş tek bir DNA kaydıdır.",
    analogy: "Bir cümledeki harflerin sırası gibi: harfler aynı olsa bile sıra değişince anlam değişir.",
  },
  {
    id: "nukleotid", term: "Nükleotid (A, C, G, T)", aka: "baz", group: "DNA ve barkod",
    short: "DNA'nın yapıtaşı. Dört çeşidi vardır ve harflerle gösterilir: A, C, G, T.",
    more: "Bir dizideki her harf bir nükleotittir (\"baz\" da denir). Okunamayan ya da belirsiz kalan yerler N harfiyle gösterilir; çok fazla N içeren diziler bu sitede elenmiştir. Dizi uzunlukları bp (baz çifti) ile yazılır.",
    analogy: "Dört harfli bir alfabe.",
  },
  {
    id: "bp", term: "bp (baz çifti)", aka: "base pair baz çifti", group: "DNA ve barkod",
    short: "DNA uzunluk birimi: bir nükleotid çifti (karşılıklı iki harf) bir baz çiftidir.",
    more: "Sitede bir dizinin uzunluğu bp olarak yazılır. Örneğin 600 bp, yaklaşık 600 harflik bir DNA parçası demektir.",
  },
  {
    id: "gen-bolge", term: "Gen / bölge", group: "DNA ve barkod",
    short: "Gen, bir görevi (örneğin bir proteini) kodlayan DNA parçasıdır; \"bölge\" ise DNA üzerindeki herhangi bir belirli parçadır.",
    more: "Barkod olarak seçilen parçalardan bazıları gendir (rbcL, matK), bazıları ise genlerin arasındaki ayırıcı bölgedir (ITS). Bu yüzden sitede genel olarak \"barkod bölgesi\" denir.",
  },
  {
    id: "kloroplast", term: "Kloroplast", aka: "plastid", group: "DNA ve barkod",
    short: "Bitki hücresinde fotosentez yapan, kendi küçük DNA'sı olan organel.",
    more: "rbcL ve matK kloroplast DNA'sında bulunur; ITS ise hücre çekirdeğindeki DNA'dadır.",
  },
  // ---- Barkod bölgeleri
  {
    id: "barkod-bolgesi", term: "Barkod bölgesi (marker)", aka: "marker", group: "Barkod bölgeleri",
    short: "Türleri karşılaştırmak için seçilmiş standart DNA bölümü. Sitede \"marker\" sözcüğü de aynı anlama gelir.",
    more: "Bu sitede üç barkod bölgesi incelenir: rbcL, matK ve ITS. Her biri ayrı ayrı ve bazı sayfalarda birlikte değerlendirilir.",
    analogy: "Aynı sorulara bakan üç ayrı \"kimlik kontrolü\" gibi: biri bazı türleri ayırabilir, biri başka türleri.",
  },
  {
    id: "rbcl", term: "rbcL", group: "Barkod bölgeleri",
    short: "Kloroplast DNA'sında bulunan ve fotosentezde görevli RuBisCO enziminin büyük alt birimini kodlayan gen.",
    more: "Bitki barkodlamasında yaygın kullanılan bir bölgedir. Her türü ayırt etmeyebilir; bu sitede ne kadar ayırt ettiği ölçülür.",
  },
  {
    id: "matk", term: "matK", group: "Barkod bölgeleri",
    short: "Kloroplast DNA'sında bulunan, \"maturaz K\" enzimini kodlayan gen.",
    more: "rbcL gibi bitki barkodlamasında yaygın kullanılır. Sitede her tür için kaç matK dizisi bulunduğu ve bu bölgenin türleri ne kadar ayırdığı gösterilir.",
  },
  {
    id: "its", term: "ITS", aka: "internal transcribed spacer", group: "Barkod bölgeleri",
    short: "Hücre çekirdeğindeki ribozomal DNA'da, iki gen arasında bulunan ayırıcı bölge (internal transcribed spacer).",
    more: "ITS bir gen değil, genler arasındaki bir bölgedir. Bu sitede rbcL ve matK'dan ayrı bir üçüncü barkod bölgesi olarak ele alınır.",
  },
  // ---- Diziler ve veri kaynakları
  {
    id: "wcvp", term: "WCVP", aka: "World Checklist of Vascular Plants", group: "Diziler ve veri kaynakları",
    short: "Kew Kraliyet Botanik Bahçesi'nin hazırladığı \"damarlı bitkiler dünya kontrol listesi\"; sitedeki tür listesi buradan gelir.",
    more: "Bu sitede \"Türkiye florası\", WCVP'ye göre Türkiye'de doğal olarak yetişen kabul edilmiş türler olarak tanımlanır. Taksonomik görüşler zamanla değişebilir.",
  },
  {
    id: "ena", term: "ENA", aka: "European Nucleotide Archive", group: "Diziler ve veri kaynakları",
    short: "Avrupa Nükleotid Arşivi: bilim insanlarının yüklediği DNA dizilerinin herkese açık deposu (EMBL-EBI).",
    more: "Sitedeki DNA dizileri ENA'dan alınmıştır. ENA, uluslararası INSDC ağının Avrupa üyesidir.",
  },
  {
    id: "insdc", term: "GenBank / INSDC", aka: "GenBank INSDC DDBJ", group: "Diziler ve veri kaynakları",
    short: "GenBank (ABD), ENA (Avrupa) ve DDBJ (Japonya) birlikte INSDC ağını oluşturur ve DNA dizilerini birbiriyle paylaşır.",
    more: "Bir dizi bu arşivlerin birine yüklendiğinde diğerlerinde de görünür. Kayıtlar yükleyen kişilerin bildirdiği adlara dayanır ve doğrulanmaz.",
  },
  {
    id: "erisim-numarasi", term: "Erişim numarası (accession)", aka: "accession", group: "Diziler ve veri kaynakları",
    short: "Arşivdeki her DNA kaydına verilen benzersiz kimlik (harf ve rakamlardan oluşur).",
    more: "Sitede bir diziye tıklayınca bu numarayla kaydın özgün sayfasına gidebilirsiniz. Dizinin kaynağına atıf yapmak için bu numara kullanılır.",
    analogy: "Kitabın ISBN numarası ya da kargo takip numarası gibi.",
  },
  {
    id: "fasta", term: "FASTA", group: "Diziler ve veri kaynakları",
    short: "DNA dizilerini düz metin olarak yazmanın basit biçimi: \">\" ile başlayan bir ad satırı, ardından dizinin harfleri.",
    more: "Dizi arama sayfasına dizinizi FASTA biçiminde ya da yalnızca harfler olarak yapıştırabilirsiniz.",
  },
  {
    id: "referans-dizi", term: "Referans dizi", group: "Diziler ve veri kaynakları",
    short: "Karşılaştırma için kullanılan, adı bilinen türe ait kayıtlı dizi.",
    more: "Dizi arama sayfasında sizin dizinizle karşılaştırılan diziler, sitenin verisindeki bu kayıtlardır.",
  },
  {
    id: "turkiye-ornegi", term: "Türkiye örneği", group: "Diziler ve veri kaynakları",
    short: "Kaydında örneğin Türkiye'den toplandığı yazan dizi.",
    more: "Dizilerin çoğu başka ülkelerdeki örneklerden gelir. Bu, Türkiye'deki bitkilerin gerçek çeşitliliğinin tam yansımayabileceği anlamına gelir.",
  },
  {
    id: "hatali-kayit", term: "Hatalı tanımlanmış kayıt", group: "Diziler ve veri kaynakları",
    short: "Arşivde yanlış tür adıyla kaydedilmiş dizi.",
    more: "Arşivlerdeki adlar yükleyen kişinin bildirimine dayanır; sitede ayrıca doğrulanmaz. Bu tür kayıtlar sonuçları bozabilir.",
  },
  {
    id: "orneklem", term: "Örneklem", group: "Diziler ve veri kaynakları",
    short: "İncelenen kayıtların tümü ya da bir türden elimizde bulunan dizilerin sayısı.",
    more: "Bir türden yalnızca bir ya da iki dizi varsa, o türün tüm doğal çeşitliliğini temsil etmez; bu yüzden sonuçlar daha az güvenilirdir.",
    analogy: "Bir sınıfın yalnızca iki öğrencisine bakarak tüm okulu tanımaya çalışmak gibi.",
  },
  {
    id: "veri-boslugu", term: "Veri boşluğu", group: "Diziler ve veri kaynakları",
    short: "Henüz DNA barkodu bulunmayan tür, cins ya da aile.",
    more: "Boşluk, o türün önemsiz olduğunu değil, yalnızca arşivlerde uygun dizisinin bulunmadığını gösterir. Veri boşlukları sayfası bunları listeler.",
    analogy: "Kütüphane kataloğunda henüz fişi çıkarılmamış kitaplar gibi.",
  },
  // ---- Mesafe ve ağaç
  {
    id: "hizalama", term: "Hizalama", group: "Mesafe ve ağaç",
    short: "Farklı dizileri, benzer yerleri alt alta gelecek biçimde yan yana dizmek.",
    more: "Dizilerin uzunlukları ve başlangıçları farklı olabilir; karşılaştırma yapabilmek için önce hizalanırlar.",
    analogy: "İki metni, aynı sözcükler karşı karşıya gelecek şekilde alt alta yazmak gibi.",
  },
  {
    id: "mafft", term: "MAFFT", group: "Mesafe ve ağaç",
    short: "Çok sayıda DNA dizisini hizalayan bir bilgisayar programı.",
    more: "Hangi hizalama yöntemiyle hesaplandığı, ilgili sayfalarda \"hizalama\" bilgisi olarak belirtilir.",
  },
  {
    id: "p-mesafesi", term: "Genetik mesafe (p-mesafesi)", aka: "p-mesafe", group: "Mesafe ve ağaç",
    short: "İki hizalanmış dizide farklı olan harflerin, karşılaştırılabilen harflere oranı.",
    more: "Sıfır, karşılaştırılan bölgede hiç fark olmadığı demektir. Sayı büyüdükçe diziler birbirinden daha çok ayrışır. Boşluklar ve belirsiz (N) harfler hesaba katılmaz.",
    analogy: "İki metindeki farklı harflerin oranı gibi. %1 mesafe, her 100 harften yaklaşık 1'inin farklı olması demektir.",
  },
  {
    id: "en-yakin-komsu", term: "Eşiksiz en-yakın-komşu", aka: "en yakın komşu nearest neighbour", group: "Mesafe ve ağaç",
    short: "Her dizi için, diğer tüm dizilerle mesafe hesaplanır ve en yakın olan bulunur; en yakın dizi aynı türdense o dizi için tür ayırt edilmiş sayılır.",
    more: "Bu sitede mesafe eşiği yoktur ve \"eşleşme yok\" sınıfı kullanılmaz (eşikli \"best close match\" yönteminden farkı budur). En yakını başka bir türe aitse başarısız, aynı mesafeyle hem kendi türüne hem başka türe yakınsa belirsiz sayılır. Karşılaştırma aynı aile içinde (büyük ailelerde aynı cins içinde) yapılır.",
    analogy: "Bir kalabalıkta size en çok benzeyen kişinin kardeşiniz olup olmadığına bakmak gibi.",
  },
  {
    id: "ayirt-edilebilirlik", term: "Ayırt edilebilirlik (başarı oranı)", group: "Mesafe ve ağaç",
    short: "Bir barkod bölgesinin, türleri birbirinden ayırabildiği durumların oranı.",
    more: "Yalnızca birden çok dizisi olan türler değerlendirilir. Dizi düzeyinde oran, en yakın komşusu kendi türünden olan dizilerin oranıdır; tür düzeyinde ise bir türün tüm dizilerinin bu sınamayı geçmesi gerekir. Oran yüksek olsa bile her tür için kesin tanı anlamına gelmez.",
  },
  {
    id: "filogenetik-agac", term: "Filogenetik ağaç (akrabalık ağacı)", aka: "filogeni", group: "Mesafe ve ağaç",
    short: "Dizilerin birbirine benzerliğini dallanan bir ağaç şeklinde gösteren çizim.",
    more: "Bu sitedeki ağaçlar, tek bir kısa barkod bölgesinin benzerliğinden hesaplanır; bu yüzden akrabalığın kesin kanıtı değil, bir ipucudur.",
    analogy: "Bir aile soy ağacına benzer; fakat burada yalnızca harf benzerliğine bakılır.",
  },
  {
    id: "dal-yaprak-dugum", term: "Dal, yaprak, düğüm", aka: "dal yaprak düğüm", group: "Mesafe ve ağaç",
    short: "Yaprak ağacın ucudur (bir dizi, etiketinde tür adı yazar); düğüm dalların ayrıldığı noktadır; dal ise iki nokta arasındaki çizgidir.",
    more: "Birbirine yakın yapraklar, dizileri birbirine benzeyen kayıtlardır. Aynı türün birden fazla dizisi ağaçta birden fazla yaprak olarak görünür.",
  },
  {
    id: "nj", term: "Komşu birleştirme (NJ)", aka: "neighbor-joining NJ", group: "Mesafe ve ağaç",
    short: "Mesafe tablosundan hızlı bir şekilde ağaç kuran yöntem (neighbor-joining).",
    more: "Sitedeki ağaçlar bu yöntemle kurulur ve orta noktadan köklendirilir. Hızlı ve basit bir yöntemdir; ağacın kesin akrabalık gösterdiği anlamına gelmez.",
  },
  {
    id: "mesafeli-gorunum", term: "Mesafeli görünüm (phylogram)", aka: "phylogram", group: "Mesafe ve ağaç",
    short: "Ağacın, yatay çizgi uzunluğunun genetik farkla orantılı çizildiği hali.",
    more: "Uzun bir dal, o dizinin ötekilerden daha çok farklılaştığını gösterir. Ölçek çubuğu, belirli bir p-mesafesinin ne kadar uzunluğa karşılık geldiğini gösterir.",
  },
  {
    id: "dallanma-duzeni", term: "Dallanma düzeni (cladogram)", aka: "cladogram", group: "Mesafe ve ağaç",
    short: "Ağacın yalnızca dallanma biçimini gösteren, çizgi uzunluklarının bir anlam taşımadığı hali.",
    more: "Çok büyük ağaçlarda okumayı kolaylaştırmak için kullanılır. Bu görünümde çizgilerin uzun ya da kısa olması genetik farkı göstermez; yalnızca kimin kiminle aynı daldan ayrıldığına bakılır.",
  },
  // ---- Bitki sınıflandırması
  {
    id: "latince-ad", term: "Latince bilimsel ad", group: "Bitki sınıflandırması",
    short: "Dünyada her türe verilen iki sözcüklü ortak ad (cins + tür sıfatı); italik yazılır.",
    more: "Örneğin Pinus brutia: Pinus cins adı, brutia tür sıfatıdır. Halk adları yöreden yöreye değişebilir; bilimsel ad herkes için aynıdır.",
  },
  {
    id: "tur", term: "Tür", group: "Bitki sınıflandırması",
    short: "Canlıların sınıflandırmasında temel birim; bu sitede WCVP'nin kabul ettiği tür adları kullanılır.",
  },
  {
    id: "cins", term: "Cins", group: "Bitki sınıflandırması",
    short: "Birbirine yakın türlerin oluşturduğu grup; Latince adın ilk sözcüğüdür.",
    analogy: "Soyadı gibi: aynı cinsten türler birbirinin yakın akrabalarıdır. Örneğin Pinus brutia ile Pinus nigra aynı cinstendir.",
  },
  {
    id: "familya", term: "Familya (aile)", aka: "aile familya", group: "Bitki sınıflandırması",
    short: "Birbirine yakın cinslerin oluşturduğu daha geniş grup; adı genellikle -aceae ile biter (örneğin Pinaceae).",
    analogy: "Geniş aile: birden çok soyadı (cins) aynı geniş ailede toplanır.",
  },
  {
    id: "takson", term: "Takson", group: "Bitki sınıflandırması",
    short: "Sınıflandırmadaki herhangi bir grup: tür, cins ya da aile birer taksondur.",
  },
  {
    id: "kabul-edilmis-tur", term: "Kabul edilmiş tür", group: "Bitki sınıflandırması",
    short: "WCVP'nin şu an geçerli saydığı bilimsel ad.",
    more: "Bir tür geçmişte başka adlarla da anılmış olabilir; bu eski adlar eş anlamlı (sinonim) olarak kaydedilir.",
  },
  {
    id: "esanlamli", term: "Eşanlamlı ad (sinonim)", aka: "sinonim synonym eş ad", group: "Bitki sınıflandırması",
    short: "Aynı türe verilmiş eski ya da alternatif bilimsel ad.",
    more: "Arşivdeki kayıt eski adla yüklenmişse, bu ad tek bir kabul edilmiş Türkiye türüne gidiyorsa o türe sayılır; birden fazla türe gidiyorsa belirsiz olduğu için kullanılmaz.",
  },
  {
    id: "endemik", term: "Endemik tür", group: "Bitki sınıflandırması",
    short: "Doğal olarak yalnızca belirli bir bölgede yetişen tür; bu sitede WCVP verisine göre yalnızca Türkiye'de yetişenler.",
    more: "Endemik türler yalnızca burada bulunduğu için koruma açısından özellikle önemlidir; barkod verisi eksikse bu bilgi başka yerden tamamlanamaz. Bu sitedeki etiket WCVP yayılışına dayanır; IUCN veya Türkiye Kırmızı Listesi değerlendirmesi değildir.",
  },
  {
    id: "halk-adi", term: "Halk adı (Türkçe ad)", group: "Bitki sınıflandırması",
    short: "Halkın kullandığı ad. Aynı ad birden fazla türe verilebilir, bir tür birden çok adla anılabilir.",
    more: "Sitedeki Türkçe adlar açık kaynaklardan derlenmiştir ve bir uzman tarafından doğrulanmamıştır.",
  },
  // ---- Sonuçları okumak
  {
    id: "belirsiz-cift", term: "Belirsiz (ayırt edilemeyen) tür çifti", group: "Sonuçları okumak",
    short: "İncelenen barkod bölgesinde dizileri birbirinin aynı (mesafe 0) olan iki tür.",
    more: "Bu iki türü o bölgeye bakarak ayıramayız; başka bir bölge ya da başka bir yöntem gerekir. Bu, türlerin aynı olduğu anlamına gelmez.",
  },
  {
    id: "benzerlik", term: "Benzerlik yüzdesi (dizi arama)", aka: "identity", group: "Sonuçları okumak",
    short: "Sizin diziniz ile referans dizi hizalandığında, örtüşen bölgedeki aynı harflerin oranı.",
    more: "Yüksek benzerlik, o türün kesin olduğunu kanıtlamaz: aynı cinsten yakın türler çok benzer olabilir ve referans kayıt yanlış adlandırılmış olabilir.",
  },
  {
    id: "ters-tamamlayici", term: "Ters tamamlayıcı", group: "Sonuçları okumak",
    short: "DNA'nın karşı ipliğinin okunuşu: dizi tersten okunur ve A↔T, C↔G değişir.",
    more: "Bir dizi ters yönde yüklenmiş olabilir; dizi arama bu durumu da dener ve eşleşme böyleyse \"ters tamamlayıcı\" yazar.",
  },
];

export const GLOSSARY_BY_ID: Record<string, GlossaryEntry> = Object.fromEntries(GLOSSARY.map((g) => [g.id, g]));
